from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Literal, List, Union

from osc import core
from openqa_client.client import OpenQA_Client

from launcher.types import JobScheduledReply


API_URL = "https://api.opensuse.org/"


class Arch(Enum):
    x86_64 = "x86_64"

    def __str__(self) -> str:
        return self.value


class TestSuiteType(Enum):
    LIVE_ISO = "kiwi-test-iso"
    INSTALL_ISO = "kiwi-install-iso"
    DISK_IMAGE = "kiwi-test-disk"

    def __str__(self) -> str:
        return self.value


class EfiTestSuiteType(Enum):
    LIVE_ISO = "kiwi-test-iso-efi"
    INSTALL_ISO = "kiwi-install-iso-efi"
    DISK_IMAGE = "kiwi-test-disk-efi"

    def __str__(self) -> str:
        return self.value


def get_efi_testsuite(test_suite: TestSuiteType) -> EfiTestSuiteType:
    return {
        TestSuiteType.DISK_IMAGE: EfiTestSuiteType.DISK_IMAGE,
        TestSuiteType.INSTALL_ISO: EfiTestSuiteType.INSTALL_ISO,
        TestSuiteType.LIVE_ISO: EfiTestSuiteType.LIVE_ISO,
    }[test_suite]


@dataclass(frozen=True)
class ObsImagePackage:
    project: str
    package: str
    test_suite: TestSuiteType
    repository: str = "images"
    subdir: str = ""
    arch: Arch = Arch.x86_64
    extra_api_post_params: Dict[str, Union[str, int]] = field(
        default_factory=dict
    )
    supports_uefi: bool = True

    @staticmethod
    def new_live_iso_package(
        project: str, package: str, **kwargs
    ) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            test_suite=TestSuiteType.LIVE_ISO,
            subdir="iso",
            extra_api_post_params=kwargs.pop("extra_api_post_params", dict()),
            **kwargs,
        )

    @staticmethod
    def new_install_iso_package(
        project: str,
        package: str,
        **kwargs,
    ) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            test_suite=TestSuiteType.INSTALL_ISO,
            subdir="iso",
            extra_api_post_params=kwargs.pop("extra_api_post_params", dict()),
            **kwargs,
        )

    @staticmethod
    def new_disk_image_package(
        project: str,
        package: str,
        **kwargs,
    ) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            test_suite=TestSuiteType.DISK_IMAGE,
            extra_api_post_params=kwargs.pop("extra_api_post_params", dict()),
            **kwargs,
        )

    def get_download_url(self, use_https: bool) -> str:
        binaries_of_pkg = [
            binary
            for binary in core.get_binarylist(
                API_URL,
                self.project,
                self.repository,
                str(self.arch),
                self.package,
            )
            if binary[-4:] == ".iso"
            or binary[-3:] == ".xz"
            or binary[-6:] == ".qcow2"
            or binary[-4:] == ".raw"
        ]

        published_binaries = core.get_binarylist_published(
            API_URL, self.project, self.repository, self.subdir
        )

        published_binaries_of_pkg = set(binaries_of_pkg).intersection(
            set(published_binaries)
        )

        if (l := len(published_binaries_of_pkg)) != 1:
            raise RuntimeError(
                f"Expected one published binary for {self.package}, but got {l}: "
                + ", ".join(published_binaries_of_pkg)
            )

        binary = published_binaries_of_pkg.pop()
        if self.test_suite in (
            TestSuiteType.INSTALL_ISO,
            TestSuiteType.LIVE_ISO,
        ):
            if binary[-4:] != ".iso":
                raise RuntimeError(
                    f"Expected to find an iso for {self.package}, but got: "
                    + binary
                )

        else:
            assert self.test_suite == TestSuiteType.DISK_IMAGE
            if (
                binary[-3:] != ".xz"
                and binary[-6:] != ".qcow2"
                and binary[-4:] != ".raw"
            ):
                raise RuntimeError(
                    f"Expected to find a disk image for {self.package}, but got: "
                    + binary
                )

        return (
            f"http{'s' if use_https else ''}://download.opensuse.org/repositories"
            f"/{self.project.replace(':', ':/')}/{self.repository}"
            + ("/" + self.subdir if self.subdir else "")
            + "/"
            + binary
        )

    def create_api_post_params(
        self, efi_mode: bool, use_https: bool = False
    ) -> Dict[str, Union[str, int]]:
        if efi_mode and not self.supports_uefi:
            raise ValueError(
                f"Cannot create api POST parameters for {self.package} in EFI mode: this image does not support EFI"
            )

        flavor = str(
            self.test_suite
            if not efi_mode
            else get_efi_testsuite(self.test_suite)
        )
        params: Dict[str, Union[str, int]] = {
            **{"FLAVOR": flavor, "PACKAGE": self.package},
            **self.extra_api_post_params,
        }
        url = self.get_download_url(use_https)
        if (
            self.test_suite == TestSuiteType.INSTALL_ISO
            or self.test_suite == TestSuiteType.LIVE_ISO
        ):
            params["ISO_1_URL"] = url
        else:
            assert self.test_suite == TestSuiteType.DISK_IMAGE
            if url[-3:] == ".xz":
                params["HDD_1_DECOMPRESS_URL"] = url
            else:
                params["HDD_1_URL"] = url
            if "vmdk" in url:
                params["QEMU_DISABLE_SNAPSHOTS"] = 1
        return params


@dataclass(frozen=True)
class UefiPflash:
    """Defines the local paths on the worker to the UEFI binaries that are
    supplied to openQA via the variables `UEFI_PFLASH_CODE` and
    `UEFI_PFLASH_VARS`.
    """

    vars: str
    code: str


#: Locations of the UEFI binaries on openSUSE
OPENSUSE_UEFI_PFLASH = UefiPflash(
    vars="/usr/share/qemu/ovmf-x86_64-vars.bin",
    code="/usr/share/qemu/ovmf-x86_64-code.bin",
)
#: Locations of the UEFI binaries on Fedora, files are provided by the
#: edk2-ovmf package
FEDORA_UEFI_PFLASH = UefiPflash(
    vars="/usr/share/edk2/ovmf/OVMF_VARS.fd",
    code="/usr/share/edk2/ovmf/OVMF_CODE.fd",
)
OpenqaHostOsT = Literal["fedora", "opensuse"]


def get_uefi_pflash(openqa_host_os: OpenqaHostOsT) -> UefiPflash:
    if openqa_host_os == "opensuse":
        return OPENSUSE_UEFI_PFLASH
    elif openqa_host_os == "fedora":
        return FEDORA_UEFI_PFLASH
    else:
        assert False, (
            f"got an invalid value for {openqa_host_os=}, "
            "allowed values are 'opensuse' and 'fedora'"
        )


@dataclass
class DistroTest:
    distri: str
    version: str
    packages: List[ObsImagePackage]

    with_uefi: bool = True
    use_https_for_asset_download: bool = False

    def _params_from_pkg(
        self, pkg: ObsImagePackage, casedir: str, build: str, efi_mode: bool
    ) -> Dict[str, Union[str, int]]:
        return {
            **pkg.create_api_post_params(
                use_https=self.use_https_for_asset_download, efi_mode=efi_mode
            ),
            "DISTRI": self.distri,
            "ARCH": str(pkg.arch),
            "VERSION": self.version,
            "PRODUCTDIR": ".",
            "CASEDIR": casedir,
            # workaround for https://progress.opensuse.org/issues/94735
            "NEEDLES_DIR": casedir,
            "BUILD": build,
            # MicroOS will refuse to install on small disks and since we use
            # HDD_1_URL for the disk, openqa will *not* use HDDSIZEGB for that
            "HDDSIZEGB_1": 20,
        }

    def trigger_tests(
        self,
        client: OpenQA_Client,
        casedir: str,
        build: str,
        dry_run: bool = False,
        openqa_host_os: OpenqaHostOsT = "opensuse",
    ) -> List[JobScheduledReply]:
        all_params = []
        for pkg in self.packages:
            all_params.append(
                {**self._params_from_pkg(pkg, casedir, build, efi_mode=False)}
            )

            if self.with_uefi and pkg.supports_uefi:
                efi_params = self._params_from_pkg(
                    pkg, casedir, build, efi_mode=True
                )
                uefi_pflash = get_uefi_pflash(openqa_host_os)
                efi_params["UEFI_PFLASH_CODE"] = uefi_pflash.code
                efi_params["UEFI_PFLASH_VARS"] = uefi_pflash.vars
                all_params.append({**efi_params})

        launched_jobs = []

        for param_dict in all_params:
            if dry_run:
                print("POST", "isos", param_dict)
            else:
                launched_jobs.append(
                    client.openqa_request(
                        "POST", "isos", param_dict, retries=0
                    )
                )

        return launched_jobs

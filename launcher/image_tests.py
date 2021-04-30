from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class ObsImagePackage:
    project: str
    package: str
    repository: str
    test_suite: TestSuiteType
    subdir: str = ""
    arch: Arch = Arch.x86_64

    @staticmethod
    def new_live_iso_package(project: str, package: str) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            repository="images",
            test_suite=TestSuiteType.LIVE_ISO,
            subdir="iso",
        )

    @staticmethod
    def new_install_iso_package(project: str, package: str) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            repository="images",
            test_suite=TestSuiteType.INSTALL_ISO,
            subdir="iso",
        )

    @staticmethod
    def new_disk_image_package(project: str, package: str) -> ObsImagePackage:
        return ObsImagePackage(
            project,
            package,
            repository="images",
            test_suite=TestSuiteType.DISK_IMAGE,
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
        ]

        published_binaries = core.get_binarylist_published(
            API_URL, self.project, self.repository, self.subdir
        )

        published_binaries_of_pkg = set(binaries_of_pkg).intersection(
            set(published_binaries)
        )

        if (l := len(published_binaries_of_pkg)) != 1:
            raise RuntimeError(
                f"Expected one published binary, but got {l}: "
                + ", ".join(published_binaries_of_pkg)
            )

        binary = published_binaries_of_pkg.pop()
        if self.test_suite in (
            TestSuiteType.INSTALL_ISO,
            TestSuiteType.LIVE_ISO,
        ):
            if binary[-4:] != ".iso":
                raise RuntimeError(
                    "Expected to find an iso, but got: " + binary
                )

        else:
            assert self.test_suite == TestSuiteType.DISK_IMAGE
            if binary[-3:] != ".xz" and binary[-6:] != ".qcow2":
                raise RuntimeError(
                    "Expected to find a disk image, but got: " + binary
                )

        return (
            f"http{'s' if use_https else ''}://download.opensuse.org/repositories"
            f"/{self.project.replace(':', ':/')}/{self.repository}"
            + ("/" + self.subdir if self.subdir else "")
            + "/"
            + binary
        )

    def create_api_post_params(
        self, use_https: bool = False
    ) -> Dict[str, Union[str, int]]:
        params: Dict[str, Union[str, int]] = {"FLAVOR": str(self.test_suite)}
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
    vars="/usr/share/qemu/ovmf-x86_64-ms-vars.bin",
    code="/usr/share/qemu/ovmf-x86_64-ms-code.bin",
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
        self, pkg: ObsImagePackage, casedir: str, build: str
    ) -> Dict[str, Union[str, int]]:
        return {
            **pkg.create_api_post_params(
                use_https=self.use_https_for_asset_download
            ),
            "DISTRI": self.distri,
            "ARCH": str(pkg.arch),
            "VERSION": self.version,
            "PRODUCTDIR": ".",
            "CASEDIR": casedir,
            # workaround for https://progress.opensuse.org/issues/94735
            "NEEDLES_DIR": casedir,
            "BUILD": build,
        }

    def trigger_tests(
        self,
        client: OpenQA_Client,
        casedir: str,
        build: str,
        dry_run: bool = False,
        openqa_host_os: OpenqaHostOsT = "opensuse",
    ) -> List[JobScheduledReply]:

        launched_jobs = []

        for pkg in self.packages:
            params = self._params_from_pkg(
                pkg,
                casedir,
                build,
            )
            if dry_run:
                print("POST", "isos", params)
            else:
                launched_jobs.append(
                    client.openqa_request("POST", "isos", params, retries=0)
                )
            if self.with_uefi:
                params["UEFI"] = 1
                uefi_pflash = get_uefi_pflash(openqa_host_os)
                params["UEFI_PFLASH_CODE"] = uefi_pflash.code
                params["UEFI_PFLASH_VARS"] = uefi_pflash.vars
                if dry_run:
                    print("POST", "isos", params)
                else:
                    launched_jobs.append(
                        client.openqa_request(
                            "POST", "isos", params, retries=1
                        )
                    )

        return launched_jobs

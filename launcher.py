#!/usr/bin/python3

import subprocess
import shlex
import re

from typing import List, Optional

from lxml import etree


def get_binaries(
    project: str, repo: str = "images", subdir: Optional[str] = None
) -> List[str]:
    cmd = f"osc api /published/{project}/{repo}"
    cmd += f"/{subdir}" if subdir is not None else ""

    osc_res = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    osc_res.check_returncode()

    all_binaries = etree.fromstring(osc_res.stdout)
    binaries = []

    binary_regex = re.compile(
        r"\S+-Build(?P<build_id>\d+\.\d+)\.(?!\S+\.sha256|\.sha256\.asc)\S+"
    )

    for entry in all_binaries.iterfind(".//entry"):
        binary_name = entry.get("name")
        if binary_name[:-4] == ".asc" or binary_name[:-11] == ".sha256.asc":
            continue
        match = binary_regex.match(binary_name)
        if match is not None:
            binaries.append(binary_name)

    return binaries


INSTALL_ISO_IMAGES = [
    "kiwi-test-image-disk",
    "kiwi-test-image-disk-legacy",
    "kiwi-test-image-custom-partitions",
]

LIVE_ISOS = [
    "kiwi-test-image-live",
    "kiwi-test-image-live-vfox",
]

DISK_IMAGES = [
    "kiwi-test-image-suse-on-dnf",
    "kiwi-test-image-lvm",
    "kiwi-test-image-MicroOS",
    "kiwi-test-image-overlayroot",
    "kiwi-test-image-qcow-openstack",
    "kiwi-test-image-disk-simple",
    "kiwi-test-image-custom-partitions",
]

INSTALL_ISO_REGEX, LIVE_ISOS_REGEX = map(
    lambda fnames: re.compile("(" + "|".join(fnames) + r")\.\S+\.iso"),
    [
        INSTALL_ISO_IMAGES,
        LIVE_ISOS,
    ],
)
DISK_IMAGE_REGEX = re.compile(
    "(" + "|".join(DISK_IMAGES) + r")\.\S+\.(qcow2|xz|vmx)"
)


def create_api_post(binary_name: str) -> Optional[str]:
    flavor: Optional[str] = None
    extra_vars: Optional[str] = None
    if INSTALL_ISO_REGEX.match(binary_name):
        flavor = "kiwi-install-iso"
        extra_vars = f"ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/{binary_name}"
    if LIVE_ISOS_REGEX.match(binary_name):
        flavor = "kiwi-test-iso"
        extra_vars = f"ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/{binary_name}"
    if DISK_IMAGE_REGEX.match(binary_name):
        flavor = "kiwi-test-disk"
        extra_vars = (
            "HDD_1_DECOMPRESS_URL="
            if binary_name[:-3] == ".xz"
            else "HDD_1_URL="
        )
        extra_vars += f"https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/{binary_name}"
        if "vmdk" in binary_name:
            extra_vars += " QEMU_DISABLE_SNAPSHOTS=1"

    if flavor is not None:
        assert extra_vars is not None
        return f'DISTRI=opensuse FLAVOR={flavor} ARCH=x86_64 VERSION=Tumbleweed PRODUCTDIR="." {extra_vars}'

    return None


if __name__ == "__main__":
    from argparse import ArgumentParser
    from datetime import datetime

    parser = ArgumentParser("kiwi-openqa-launcher")
    parser.add_argument(
        "--git-remote",
        nargs=1,
        default=["https://github.com/OSInside/kiwi-functional-tests.git"],
        type=str,
    )
    parser.add_argument("--build", nargs=1, default=[None], type=str)
    parser.add_argument("--host", nargs=1, default=[None], type=str)

    args = parser.parse_args()

    build = args.build[0] or datetime.now().strftime("%Y%m%d")

    for binary in get_binaries(
        "Virtualization:Appliances:Images:Testing_x86:suse"
    ) + get_binaries(
        "Virtualization:Appliances:Images:Testing_x86:suse", subdir="iso"
    ):
        api_post = create_api_post(binary)
        if api_post:
            cmd = f"openqa-cli api{' --host ' + args.host[0] if args.host[0] is not None else ''} -X POST isos {api_post} BUILD={build} CASEDIR={args.git_remote[0]}"
            print(cmd)

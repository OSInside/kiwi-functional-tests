"""Module containing the definitions of the kiwi test suites, job groups and
products.

The kiwi tests are currently structured as follows:
We have 3 base test suites:
- `kiwi_disk_image_test`: this test suite is intended for various disk images
                          that kiwi produces. openQA boots from these, logs in,
                          reboots them and tries the same again.
- `kiwi_install_test`: this is a test suite for unattended installation
                       ISOs. openQA boots from them and waits for the
                       installation to finish.
- `kiwi_live_image_test`: a test suite for live ISOs that are booted, then
                          openQA logs in and shuts them down again.


We want to run the above test suites for a combination of distributions and
versions. We achieve this by creating a medium/product for each distribution +
version combination that we want to test. The distribution + version
combination is available in :ref:`KIWI_DISTRO_MATRIX`. From this we create the
list of mediums/products and store it in :ref:`KIWI_PRODUCTS` as well as the
job template for the kiwi job group (see :ref:`KIWI_JOB_TEMPLATE`).
"""

from itertools import product
from typing import Dict, List, Tuple, Union

from launcher.types import Product, TestSuite
from launcher.image_tests import DistroTest, ObsImagePackage


SIXTY_FOUR_BIT_MACHINE_SETTINGS = {
    "name": "64bit",
    "backend": "qemu",
    "settings": [
        {"key": "HDDSIZEGB", "value": 20},
        {"key": "QEMUCPU", "value": "qemu64"},
        {"key": "VIRTIO_CONSOLE", "value": 1},
        {"key": "WORKER_CLASS", "value": "qemu_x86_64"},
    ],
}


#: the name of the kiwi job group on openQA
KIWI_JOB_GROUP_NAME = "kiwi images"

#: dictionary of openQA test suites
#: the key is the test suite name and the value are the settings that need to
#: be applied
KIWI_TEST_SUITES: Dict[str, TestSuite] = {
    "kiwi_disk_image_test": {
        "description": "Test a disk image produced by kiwi",
        "settings": [],
    },
    "kiwi_install_test": {
        "description": "Runs the installation from a kiwi disk image",
        "settings": [
            {
                "key": "PUBLISH_HDD_1",
                "value": "%DISTRI%-%VERSION%-%ARCH%-%BUILD%.qcow2",
            }
        ],
    },
    "kiwi_live_image_test": {
        "description": "Tests of the kiwi live images",
        "settings": [],
    },
}

OPENSUSE_DISTRI = "opensuse"
OPENSUSE_TUMBLEWEED_VERSION = "Tumbleweed"
OPENSUSE_LEAP_VERSION = "Leap"

FEDORA_DISTRI = "fedora"
FEDORA_RAWHIDE_VERSION = "Rawhide"
FEDORA_RELEASED_VERSION = "34"

SLE_DISTRI = "sle"
SLE_15_VERSION = "15"


#: List of all tuples ($version, $distri) that are included in the kiwi test
#: suite
KIWI_DISTRO_MATRIX: List[Tuple[str, str]] = (
    list(
        product(
            (OPENSUSE_TUMBLEWEED_VERSION, OPENSUSE_LEAP_VERSION),
            [OPENSUSE_DISTRI],
        )
    )
    + list(
        product(
            (FEDORA_RELEASED_VERSION, FEDORA_RAWHIDE_VERSION), [FEDORA_DISTRI]
        )
    )
    + [(SLE_15_VERSION, SLE_DISTRI)]
)

#: all product flavors used (these are closely related to the respective test
#: suites)
KIWI_FLAVORS = [
    "kiwi-test-iso",
    "kiwi-test-disk",
    "kiwi-install-iso",
]


#: All products that we use in the kiwi test suite.
#: We create one product for all permutations of $flavor, $distri and $version
#: from :ref:`KIWI_FLAVORS` and :ref:`KIWI_DISTRO_MATRIX`
KIWI_PRODUCTS: List[Product] = [
    Product(version=version, distri=distri, flavor=flavor)
    for flavor in KIWI_FLAVORS
    for version, distri in KIWI_DISTRO_MATRIX
]


#: The YAML schedule of the kiwi job group
#:
#: This is the part that is responsible for scheduling test suites for
#: products. We perform that as follows:
#: - Installation isos get assigned the `kiwi_live_image_test` test suite with
#:   `PUBLISH_HDD_1` set, so that the resulting disk image is saved and can be
#:   re-used. After that the `kiwi_disk_image_test` test suite is scheduled
#:   booting from the previously generated disk image.
#: - disk images get scheduled with the `kiwi_disk_image_test` suite, which
#:   just boots from these
#: - for live isos we schedule the `kiwi_live_image_test` suite.
#:
#: We auto-generate this YAML schedule for each version & distri combination in
#: :ref:`KIWI_DISTRO_MATRIX`.
KIWI_JOB_TEMPLATE = (
    """defaults:
  x86_64:
    machine: 64bit
    priority: 60

products:"""
    + "\n".join(
        f"""
  kiwi-{distri}-{version}-live-iso-x86_64:
    distri: {distri}
    version: {version}
    flavor: kiwi-test-iso
  kiwi-{distri}-{version}-install-iso-x86_64:
    distri: {distri}
    version: {version}
    flavor: kiwi-install-iso
  kiwi-{distri}-{version}-disk-x86_64:
    distri: {distri}
    version: {version}
    flavor: kiwi-test-disk
"""
        for version, distri in KIWI_DISTRO_MATRIX
    )
    + """
scenarios:
  x86_64:
"""
    + "\n".join(
        f"""
    kiwi-{distri}-{version}-live-iso-x86_64:
      - kiwi_live_image_test:
          description: {KIWI_TEST_SUITES['kiwi_live_image_test']['description']} for {distri} {version}

    kiwi-{distri}-{version}-install-iso-x86_64:
      - kiwi_live_image_test:
          description: {KIWI_TEST_SUITES['kiwi_live_image_test']['description']} for {distri} {version}
          settings:
            PUBLISH_HDD_1: "%DISTRI%-%VERSION%-%PACKAGE%-%ARCH%-%BUILD%.qcow2"

      - kiwi_disk_image_test:
          description: {KIWI_TEST_SUITES['kiwi_disk_image_test']['description']} for {distri} {version}
          settings:
            HDD_1: "%DISTRI%-%VERSION%-%PACKAGE%-%ARCH%-%BUILD%.qcow2"
            START_AFTER_TEST: kiwi_live_image_test

    kiwi-{distri}-{version}-disk-x86_64:
      - kiwi_disk_image_test:
          description: {KIWI_TEST_SUITES['kiwi_disk_image_test']['description']} for {distri} {version}

"""
        for version, distri in KIWI_DISTRO_MATRIX
    )
)


RAMDISK_EXTRA_PARAMS: Dict[str, Union[str, int]] = {"QEMURAM": 4096}
LEGACY_EXTRA_PARAMS: Dict[str, Union[str, int]] = {"QEMURAM": 2048}

TUMBLEWEED_OBS_PACKAGES = (
    [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package=package,
        )
        for package in [
            "test-image-MicroOS",
            "test-image-custom-partitions",
            "test-image-disk",
            "test-image-disk-simple",
            "test-image-luks",
            "test-image-lvm",
            "test-image-orthos",
            "test-image-overlayroot",
            # FIXME: pxe? "test-image-pxe"
            "test-image-suse-on-dnf",
            "test-image-raid",
            "test-image-bundle-format",
        ]
    ]
    + [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-disk-legacy",
            extra_api_post_params=LEGACY_EXTRA_PARAMS,
        ),
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-disk-ramdisk",
            extra_api_post_params=RAMDISK_EXTRA_PARAMS,
        ),
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-qcow-openstack",
            supports_uefi=False,
        ),
    ]
    + [
        ObsImagePackage.new_install_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package=package,
        )
        for package in [
            "test-image-MicroOS",
            "test-image-custom-partitions",
            "test-image-disk",
            "test-image-raid",
        ]
    ]
    + [
        ObsImagePackage.new_install_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-disk-legacy",
            extra_api_post_params=LEGACY_EXTRA_PARAMS,
        ),
    ]
    + [
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-live:BIOS",
        ),
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-live:Standard",
        ),
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-live:Secure",
        ),
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:tumbleweed",
            package="test-image-disk-ramdisk",
            extra_api_post_params=RAMDISK_EXTRA_PARAMS,
        ),
    ]
)
OPENSUSE_TUMBLEWEED_TESTS = DistroTest(
    OPENSUSE_DISTRI, OPENSUSE_TUMBLEWEED_VERSION, TUMBLEWEED_OBS_PACKAGES
)

LEAP_OBS_PACKAGES = (
    [
        ObsImagePackage.new_install_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:leap",
            package=package,
        )
        for package in [
            "test-image-custom-partitions",
            "test-image-disk",
            "test-image-manu",
        ]
    ]
    + [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:leap",
            package=package,
        )
        for package in [
            "test-image-custom-partitions",
            "test-image-disk",
            "test-image-disk-simple",
            "test-image-luks",
            "test-image-lvm",
            "test-image-manu",
            "test-image-overlayroot",
        ]
    ]
    + [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:leap",
            package="test-image-disk-ramdisk",
            extra_api_post_params=RAMDISK_EXTRA_PARAMS,
        )
    ]
    + [
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:leap",
            package="test-image-live",
        )
    ]
    + [
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:leap",
            package="test-image-disk-ramdisk",
            extra_api_post_params=RAMDISK_EXTRA_PARAMS,
        )
    ]
)
OPENSUSE_LEAP_TESTS = DistroTest(
    OPENSUSE_DISTRI, OPENSUSE_LEAP_VERSION, LEAP_OBS_PACKAGES
)


FEDORA_RELEASED_PACKAGES = (
    [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:fedora",
            package=package,
        )
        for package in [
            "test-image-live-disk:Disk",
            "test-image-live-disk:Virtual",
            "test-image-microdnf",
        ]
    ]
    + [
        ObsImagePackage.new_install_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:fedora",
            package=package,
        )
        for package in ["test-image-live-disk:Disk"]
    ]
    + [
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:fedora",
            package=package,
        )
        for package in ["test-image-live-disk:Live"]
    ]
)
FEDORA_RELEASED_TESTS = DistroTest(
    FEDORA_DISTRI, FEDORA_RELEASED_VERSION, FEDORA_RELEASED_PACKAGES
)

FEDORA_RAWHIDE_PACKAGES = (
    [
        ObsImagePackage.new_disk_image_package(
            project="Virtualization:Appliances:Images:Testing_x86:rawhide",
            package=package,
        )
        for package in [
            "test-image-live-disk:Disk",
            "test-image-live-disk:Virtual",
            "test-image-microdnf",
        ]
    ]
    + [
        ObsImagePackage.new_install_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:rawhide",
            package=package,
        )
        for package in ["test-image-live-disk:Disk"]
    ]
    + [
        ObsImagePackage.new_live_iso_package(
            project="Virtualization:Appliances:Images:Testing_x86:rawhide",
            package=package,
        )
        for package in ["test-image-live-disk:Live"]
    ]
)
FEDORA_RAWHIDE_TESTS = DistroTest(
    FEDORA_DISTRI, FEDORA_RAWHIDE_VERSION, FEDORA_RAWHIDE_PACKAGES
)


SLE_15_PACKAGES = [
    ObsImagePackage.new_disk_image_package(
        project="Virtualization:Appliances:Images:Testing_x86:sle15",
        package="test-image-disk",
    ),
    ObsImagePackage.new_install_iso_package(
        project="Virtualization:Appliances:Images:Testing_x86:sle15",
        package="test-image-disk",
    ),
]


SLE_15_TESTS = DistroTest(
    distri=SLE_DISTRI, version=SLE_15_VERSION, packages=SLE_15_PACKAGES
)

ALL_TESTS: List[DistroTest] = [
    OPENSUSE_TUMBLEWEED_TESTS,
    OPENSUSE_LEAP_TESTS,
    FEDORA_RAWHIDE_TESTS,
    FEDORA_RELEASED_TESTS,
    SLE_15_TESTS,
]


class COLORS:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

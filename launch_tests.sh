#!/bin/bash

set -euox pipefail

export casedir='https://github.com/dcermak/kiwi-functional-tests#basic_functional_test'

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-install-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-disk.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-live.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-live-vfox.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-live-vfox.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

# have to set QEMU_DISABLE_SNAPSHOTS=1 for vmdk disks, as they are not migratable
openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_DECOMPRESS_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-suse-on-dnf.x86_64.vmdk.xz \
    QEMU_DISABLE_SNAPSHOTS=1 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_DECOMPRESS_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-disk-simple.x86_64.vmdk.xz \
    QEMU_DISABLE_SNAPSHOTS=1 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_DECOMPRESS_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-lvm.x86_64.vmdk.xz \
    QEMU_DISABLE_SNAPSHOTS=1 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-MicroOS.x86_64.qcow2 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_DECOMPRESS_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-overlayroot.x86_64.vmdk.xz \
    QEMU_DISABLE_SNAPSHOTS=1 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-qcow-openstack.x86_64.qcow2 \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

# openqa cannot boot from this:
openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-disk-simple.x86_64.vmx \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

# openqa does not like to boot from this one:
openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-test-disk ARCH=x86_64 VERSION=Tumbleweed \
    HDD_1_DECOMPRESS_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/kiwi-test-image-custom-partitions.x86_64.raw.xz \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

# these two appear to be borked:
openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-install-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-disk-legacy.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

openqa-cli api -X POST isos \
    DISTRI=opensuse FLAVOR=kiwi-install-iso ARCH=x86_64 VERSION=Tumbleweed \
    ISO_1_URL=https://download.opensuse.org/repositories/Virtualization:/Appliances:/Images:/Testing_x86:/suse/images/iso/kiwi-test-image-custom-partitions.x86_64.iso \
    CASEDIR=${casedir} \
    PRODUCTDIR=.

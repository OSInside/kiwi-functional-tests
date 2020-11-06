# kiwi-functional-tests

KIWI openQA functional tests using the images from the staging project on OBS.


## setup on openQA

### Medium types

The following 3 medium types have to be setup:
- `kiwi-test-iso`
- `kiwi-test-disk`
- `kiwi-install-iso`

all have the following settings:
- Distri: `opensuse`
- Version: `Tumbleweed`
- Arch: `x86_64`
- Settings: nothing

### Test suites

Add these 3 test suites to openQA:
- `kiwi_disk_image_test`: no additional settings
- `kiwi_install_test`: `PUBLISH_HDD_1=%DISTRI%-%VERSION%-%ARCH%-%BUILD%.qcow2`
- `kiwi_live_image_test`: no additional settings

### Jop templates

The following job template has to be setup for the job group "kiwi images" group:

```yaml
defaults:
  x86_64:
    machine: 64bit
    priority: 50

products:
  kiwi-live-iso-x86_64:
    distri: opensuse
    version: Tumbleweed
    flavor: kiwi-test-iso
  kiwi-test-install-iso-x86_64:
    distri: opensuse
    version: Tumbleweed
    flavor: kiwi-install-iso
  kiwi-test-disk-x86_64:
    distri: opensuse
    version: Tumbleweed
    flavor: kiwi-test-disk

scenarios:
  x86_64:
    kiwi-live-iso-x86_64:
      - kiwi_live_image_test

    kiwi-test-install-iso-x86_64:
      - kiwi_live_image_test:
          settings:
            PUBLISH_HDD_1: "%DISTRI%-%VERSION%-%ARCH%-%BUILD%.qcow2"
      - kiwi_disk_image_test:
          settings:
            HDD_1: "%DISTRI%-%VERSION%-%ARCH%-%BUILD%.qcow2"
            START_AFTER_TEST: kiwi_live_image_test
            +ISO_1: ""
            +ISO_1_URL: ""

    kiwi-test-disk-x86_64:
      - kiwi_disk_image_test
```

## Schedule a test run

Configure your openQA client to use the correct openQA instance by default, set
the `casedir` variable in `launch_tests.sh` to point to the correct repository &
branch and start the script `launch_tests.sh`.

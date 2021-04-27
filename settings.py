#!/usr/bin/env python3
from typing import Dict, List, TypedDict


from openqa_client.client import OpenQA_Client


class TestSuite(TypedDict):
    description: str
    settings: List[Dict[str, str]]


class Product(TypedDict):
    arch: str
    distri: str
    version: str
    settings: List[Dict[str, str]]


class Client(OpenQA_Client):
    def openqa_request(self, method, path, params=None, data=None):
        return super().openqa_request(
            method, path, params=params, retries=0, wait=0, data=data
        )


DEFAULT_PRODUCT = Product(
    arch="x86_64", version="Tumbleweed", distri="opensuse", settings=[]
)


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


KIWI_PRODUCTS: Dict[str, Product] = {
    "kiwi-test-iso": DEFAULT_PRODUCT,
    "kiwi-test-disk": DEFAULT_PRODUCT,
    "kiwi-install-iso": DEFAULT_PRODUCT,
}


KIWI_JOB_TEMPLATE = """defaults:
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
"""

KIWI_JOB_GROUP_NAME = "kiwi images"


def ensure_kiwi_settings(client: OpenQA_Client) -> None:

    test_suites = client.openqa_request("GET", "test_suites")["TestSuites"]

    for suite_name in KIWI_TEST_SUITES:
        matching_suites = list(
            filter(lambda s: s["name"] == suite_name, test_suites)
        )
        params = {**KIWI_TEST_SUITES[suite_name], "name": suite_name}
        if len(matching_suites) > 1:
            raise ValueError(
                f"Found {len(matching_suites)} with the name {suite_name}"
            )
        elif len(matching_suites) == 1:
            client.openqa_request(
                "POST",
                f"test_suites/{matching_suites[0]['id']}",
                params=params,
            )
        else:
            client.openqa_request("POST", "test_suites", params=params)

    products = client.openqa_request("GET", "products")["Products"]
    for product_flavor in KIWI_PRODUCTS:
        matching_products = list(
            filter(lambda p: p["flavor"] == product_flavor, products)
        )
        params = {**KIWI_PRODUCTS[product_flavor], "flavor": product_flavor}
        if len(matching_products) > 1:
            raise ValueError(
                f"Got {len(matching_products)} products with the flavor "
                f"{product_flavor}"
            )
        elif len(matching_products) == 1:
            client.openqa_request(
                "POST",
                f"products/{matching_products[0]['id']}",
                params=params,
            )
        else:
            client.openqa_request("POST", "products", params=params)

    job_groups = client.openqa_request("GET", "job_groups")
    matching_job_groups = list(
        filter(lambda g: g["name"] == KIWI_JOB_GROUP_NAME, job_groups)
    )
    if len(matching_job_groups) > 1:
        raise ValueError(
            f"Got {len(matching_job_groups)} job groups with the name "
            + KIWI_JOB_GROUP_NAME
        )
    elif len(matching_job_groups) == 1:
        grp_id = matching_job_groups[0]["id"]
        client.openqa_request(
            "PUT",
            f"job_groups/{grp_id}",
            data={
                "name": KIWI_JOB_GROUP_NAME,
            },
        )
    else:
        grp_id = client.openqa_request(
            "POST",
            "job_groups",
            data={
                "name": KIWI_JOB_GROUP_NAME,
                "template": KIWI_JOB_TEMPLATE,
            },
        )["id"]

    client.openqa_request(
        "POST",
        f"job_templates_scheduling/{grp_id}",
        data={
            "name": KIWI_JOB_GROUP_NAME,
            "template": KIWI_JOB_TEMPLATE,
            "schema": "JobTemplates-01.yaml",
        },
    )


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        "kiwi-openqa-settings",
        description="Apply the necessary settings on a openQA instance for "
        "the kiwi tests",
    )
    parser.add_argument(
        "--server", nargs=1, default=["openqa.opensuse.org"], type=str
    )
    parser.add_argument(
        "--server-scheme",
        nargs=1,
        choices=["http", "https"],
        type=str,
        default=["https"],
    )

    args = parser.parse_args()
    client = Client(server=args.server[0], scheme=args.server_scheme[0])

    ensure_kiwi_settings(client)

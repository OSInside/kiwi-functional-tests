#!/usr/bin/env python3
from openqa_client.client import OpenQA_Client

from launcher.constants import (
    KIWI_TEST_SUITES,
    KIWI_PRODUCTS,
    KIWI_JOB_GROUP_NAME,
    KIWI_JOB_TEMPLATE,
    SIXTY_FOUR_BIT_MACHINE_SETTINGS,
)


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
    for kiwi_product in KIWI_PRODUCTS:
        matching_products = list(
            filter(lambda p: kiwi_product.equal_in_db(p), products)
        )
        if len(matching_products) > 1:
            raise ValueError(
                f"Got {len(matching_products)} products matching"
                f" {kiwi_product=}"
            )
        elif len(matching_products) == 1:
            client.openqa_request(
                "PUT",
                f"products/{matching_products[0]['id']}",
                params=kiwi_product.__dict__,
            )
        else:
            client.openqa_request(
                "POST", "products", params=kiwi_product.__dict__
            )

    machines = client.openqa_request("GET", "machines")["Machines"]
    sixty_four_bit_machine = [
        machine for machine in machines if machine["name"] == "64bit"
    ]
    if len(sixty_four_bit_machine) > 1:
        raise ValueError(
            f"Got {len(sixty_four_bit_machine)} machines with the name '64bit'"
        )
    elif len(sixty_four_bit_machine) == 0:
        client.openqa_request(
            "POST", "machines", params=SIXTY_FOUR_BIT_MACHINE_SETTINGS
        )

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

    from launcher.argparser import SERVER_PARSER
    from launcher.client import NoWaitClient

    parser = ArgumentParser(
        "kiwi-openqa-settings",
        description="""Apply the necessary settings on a openQA instance for
the kiwi tests""",
        parents=[SERVER_PARSER],
    )

    args = parser.parse_args()
    client = NoWaitClient(server=args.server[0], scheme=args.server_scheme[0])

    ensure_kiwi_settings(client)

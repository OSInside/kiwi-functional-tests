#!/usr/bin/env python3

from itertools import chain
from typing import List


if __name__ == "__main__":
    from argparse import ArgumentParser
    from datetime import datetime
    from pickle import dump

    from osc import conf

    from launcher.argparser import SERVER_PARSER
    from launcher.client import NoWaitClient
    from launcher.constants import (
        ALL_TESTS,
        CENTOS_8_TESTS,
        CENTOS_9_TESTS,
        CENTOS_DISTRI,
        FEDORA_DISTRI,
        FEDORA_RELEASED_TESTS,
        FEDORA_RAWHIDE_TESTS,
        OPENSUSE_LEAP_TESTS,
        OPENSUSE_TUMBLEWEED_TESTS,
        OPENSUSE_DISTRI,
        SLE_DISTRI,
        SLE_15_TESTS,
        KIWI_DISTRO_MATRIX,
    )
    from launcher.image_tests import DistroTest
    from launcher.running_build import RunningBuild

    # initialize the config datastructures or else the fetch of the published
    # binaries fails
    conf.get_config()

    parser = ArgumentParser("kiwi-openqa-launcher", parents=[SERVER_PARSER])
    parser.add_argument(
        "--git-remote",
        help="""The git repository from which the tests are loaded.
Supports npm's git url syntax to also specify branches & revisions, see:
https://docs.npmjs.com/cli/v7/configuring-npm/package-json#git-urls-as-dependencies
""",
        nargs=1,
        default=["https://github.com/OSInside/kiwi-functional-tests.git"],
        type=str,
    )
    parser.add_argument(
        "--build",
        help="""The build id of the scheduled tests.
Defaults to today's date formated as year+month+day""",
        nargs=1,
        default=[None],
        type=str,
    )
    parser.add_argument(
        "-d",
        "--distri",
        help="""Only schedule tests for the supplied distribution.
Defaults to all distributions.""",
        default=None,
        choices=[OPENSUSE_DISTRI, FEDORA_DISTRI, SLE_DISTRI, CENTOS_DISTRI],
        nargs="+",
        type=str,
    )
    parser.add_argument(
        "-vd",
        "--version-distri",
        help="""Plus separated version+distri to be scheduled.
    """,
        choices=[
            f"{version}+{distri}" for version, distri in KIWI_DISTRO_MATRIX
        ],
        nargs="+",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--openqa-host-os",
        help="""The operating system that the openQA host is running.""",
        nargs=1,
        default=["opensuse"],
        choices=["opensuse", "fedora"],
        type=str,
    )
    parser.add_argument(
        "--dry-run",
        help="Don't launch any tests",
        action="store_true",
    )
    parser.add_argument(
        "--use-https-for-asset-download",
        help="""Use https to download the assets (ISOs & HDDs) instead of http.
Only enable this when the openQA host can reach download.opensuse.org via https
(this is **not** the case for openqa.opensuse.org).
""",
        action="store_true",
    )

    args = parser.parse_args()

    if args.distri is not None and args.version_distri is not None:
        raise UserWarning(
            "cannot specify both distri and version-distri at the same time"
        )

    build = args.build[0] or datetime.now().strftime("%Y%m%d")
    server = args.server[0]
    scheme = args.server_scheme[0]

    client = NoWaitClient(server=server, scheme=scheme)

    jobs = []

    all_tests: List[DistroTest] = []
    if args.distri is not None:
        if OPENSUSE_DISTRI in args.distri:
            all_tests += [OPENSUSE_TUMBLEWEED_TESTS, OPENSUSE_LEAP_TESTS]
        if FEDORA_DISTRI in args.distri:
            all_tests += [FEDORA_RAWHIDE_TESTS, FEDORA_RELEASED_TESTS]
        if SLE_DISTRI in args.distri:
            all_tests += [SLE_15_TESTS]
        if CENTOS_DISTRI in args.distri:
            all_tests += [CENTOS_8_TESTS, CENTOS_9_TESTS]
    elif args.version_distri is not None:
        for ver_distri in args.version_distri:
            matching_test = [
                test
                for test in ALL_TESTS
                if f"{test.version}+{test.distri}" == ver_distri
            ]
            assert len(matching_test) == 1
            all_tests += matching_test
    else:
        all_tests = ALL_TESTS

    for tests in all_tests:
        tests.use_https_for_asset_download = args.use_https_for_asset_download
        jobs += tests.trigger_tests(
            client,
            args.git_remote[0],
            build,
            dry_run=args.dry_run,
            openqa_host_os=args.openqa_host_os[0],
        )

    if not args.dry_run:
        running_build = RunningBuild(
            build=build,
            job_ids=list(chain(*[j["ids"] for j in jobs])),
            server=server,
            scheme=scheme,
        )
        filename = (
            f"kiwi_build_{build}_"
            + datetime.now().strftime("%Y_%B_%d-%H_%M_%S")
            + ".pickle"
        )
        with open(filename, "wb") as build_state_file:
            dump(running_build, build_state_file)

        print(f"Wrote build state into {filename}")

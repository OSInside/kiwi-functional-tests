#!/usr/bin/env python3

from typing import Any, Dict
from prettytable import PrettyTable


def format_dict(d: Dict[str, Any]) -> str:
    table = PrettyTable(["variable", "value"])
    table.align = "l"
    table.border = False
    table.header = False
    table.left_padding_width = 1
    table.right_padding_width = 1
    table.max_width = 120
    for k, v in d.items():
        table.add_row([k, str(v)])
    return table.get_string()


if __name__ == "__main__":
    from argparse import ArgumentParser
    from pickle import load

    from launcher.client import NoWaitClient
    from launcher.argparser import SERVER_PARSER
    from launcher.constants import COLORS
    from launcher.running_build import RunningBuild

    parser = ArgumentParser(parents=[SERVER_PARSER])

    parser.add_argument(
        "state_file",
        help="""Path to the state file of the build""",
        nargs=1,
        type=str,
    )
    parser.add_argument(
        "-p",
        "--print-state",
        help="print the states of the associated jobs",
        action="store_true",
    )
    parser.add_argument(
        "-c", "--cancel", help="cancel all running jobs", action="store_true"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Print more info to stdout",
        action="store_true",
    )

    args = parser.parse_args()

    if not args.print_state and not args.cancel:
        raise ValueError("Missing action for the monitoring script")

    with open(args.state_file[0], "rb") as state_file:
        running_build: RunningBuild = load(state_file)
    client = NoWaitClient(
        server=running_build.server, scheme=running_build.scheme
    )

    if args.print_state:
        table = PrettyTable(["test URL", "state", "result", "settings"])
        table.align = "l"

        states = running_build.get_job_states()
        for job_id in states:
            state = states[job_id]

            color = {
                "failed": COLORS.FAIL,
                "skipped": COLORS.WARNING,
                "incomplete": COLORS.FAIL,
                "passed": COLORS.OKGREEN,
                "softfailed": COLORS.OKCYAN,
                "user_cancelled": COLORS.WARNING,
            }.get(state["state"]) or COLORS.OKBLUE

            table.add_row(
                [
                    f"{client.baseurl}/tests/{job_id}",
                    f"{color}{state['state']}{COLORS.ENDC}",
                    state["result"],
                    format_dict(state["settings"])
                    if args.verbose
                    else format_dict(
                        {
                            k: state["settings"].get(k, None)
                            for k in [
                                "DISTRI",
                                "FLAVOR",
                                "VERSION",
                                "UEFI",
                                "HDD_1",
                                "ISO_1",
                            ]
                            if k in state["settings"]
                        }
                    ),
                ]
            )
        print(table)

    if args.cancel:
        running_build.cancel_all_jobs()

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


def main() -> None:
    from argparse import ArgumentParser
    from json import loads

    from launcher.client import NoWaitClient
    from launcher.constants import COLORS
    from launcher.running_build import RunningBuild

    parser = ArgumentParser()

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
        "-f",
        "--failed-only",
        help="only print failed jobs",
        action="store_true",
    )
    parser.add_argument(
        "-c", "--cancel", help="cancel all running jobs", action="store_true"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Print more info to stdout",
        action="count",
        default=0,
    )
    parser.add_argument(
        "--no-resolve-clones",
        help="Don't follow job clones",
        action="store_true",
    )

    args = parser.parse_args()

    if not args.print_state and not args.cancel:
        raise ValueError("Missing action for the monitoring script")

    with open(args.state_file[0], "r") as state_file:
        running_build = RunningBuild(**loads(state_file.read()))
        if not args.no_resolve_clones:
            running_build = running_build.fetch_cloned_build()

    client = NoWaitClient(
        server=running_build.server, scheme=running_build.scheme
    )

    if args.print_state:
        table = PrettyTable(["test URL", "state", "result", "settings"])
        table.align = "l"

        jobs = running_build.fetch_job_states()
        for job_id in jobs:
            job = jobs[job_id]

            if args.failed_only and job.result in (
                "scheduled",
                "softfailed",
                "passed",
                "none",
                "parallel_restarted",
                "user_restarted",
            ):
                continue

            color = {
                "failed": COLORS.FAIL,
                "skipped": COLORS.WARNING,
                "incomplete": COLORS.FAIL,
                "passed": COLORS.OKGREEN,
                "softfailed": COLORS.OKCYAN,
                "user_cancelled": COLORS.WARNING,
            }.get(job.state, COLORS.OKBLUE)

            if args.verbose == 0:
                last_col = f"{job.settings['DISTRI']} {job.settings['VERSION']}: {(job.settings.get('HDD_1') or job.settings['ISO_1'])}"
            elif args.verbose == 1:
                last_col = format_dict(
                    {
                        k: job.settings.get(k, None)
                        for k in [
                            "DISTRI",
                            "FLAVOR",
                            "VERSION",
                            "UEFI",
                            "HDD_1",
                            "ISO_1",
                        ]
                        if k in job.settings
                    }
                )
            else:
                last_col = format_dict(job.settings)

            table.add_row(
                [
                    f"{client.baseurl}/tests/{job_id}",
                    f"{color}{job.state}{COLORS.ENDC}",
                    job.result,
                    last_col,
                ]
            )
        print(table)

    if args.cancel:
        running_build.cancel_all_jobs()

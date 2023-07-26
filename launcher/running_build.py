from __future__ import annotations

from dataclasses import dataclass

from openqa_client.client import OpenQA_Client

from launcher.client import NoWaitClient
from launcher.openqa import Job, fetch_job


@dataclass
class CancelFailure:
    job_id: int
    error: Exception

    def __str__(self) -> str:
        return f"Failed to cancel job {self.job_id}, got {self.error}"


@dataclass
class RunningBuild:
    build: str
    server: str
    job_ids: list[int]
    scheme: str = ""

    @property
    def _client(self) -> NoWaitClient:
        return NoWaitClient(server=self.server, scheme=self.scheme)

    @staticmethod
    def _fetch_final_clone(client: OpenQA_Client, job: Job) -> Job:
        if not job.clone_id:
            return job
        return RunningBuild._fetch_final_clone(
            client, fetch_job(client, job.clone_id)
        )

    def fetch_cloned_build(self) -> RunningBuild:
        new_ids: list[int] = []
        deny_list = []
        client = self._client

        for job_id in self.job_ids:
            if job_id in deny_list:
                continue

            job = fetch_job(client, job_id)
            if job.clone_id:
                deny_list.extend(job.children.chained)
                new_ids.append(
                    (
                        cloned_job := RunningBuild._fetch_final_clone(
                            client, job
                        )
                    ).id
                )
                new_ids.extend(cloned_job.children.chained)

            else:
                new_ids.append(job.id)

        return RunningBuild(
            server=self.server,
            build=self.build,
            scheme=self.scheme,
            job_ids=new_ids,
        )

    def fetch_job_states(self) -> list[Job]:
        client = self._client
        return [fetch_job(client, job_id) for job_id in self.job_ids]

    def get_unfinished_jobs(self) -> list[int]:
        job_states = self.fetch_job_states()
        unfinished: list[int] = []

        for job in job_states:
            if job.state not in ("cancelled", "done"):
                unfinished.append(job.id)

        return unfinished

    def cancel_all_jobs(self) -> None:
        client = self._client
        failures = []
        for job_id in self.job_ids:
            try:
                client.openqa_request("POST", f"jobs/{job_id}/cancel")
            except Exception as exc:
                failures.append(CancelFailure(job_id, exc))

        for failure in failures:
            print(failure)

    def as_markdown(self, failed_only: bool = False) -> str:
        baseurl = self._client.baseurl
        jobs = self.fetch_job_states()
        res = """Test | state | result | settings
-----|-------|--------|---------
"""
        for job in jobs:
            if failed_only and not job.result.is_failed:
                continue

            res += (
                f"[{job.id}]({baseurl}/tests/{job.id}) | {job.state.pretty} | {job.result.pretty} | "
                + f"""{job.settings['DISTRI']} {job.settings['VERSION']}: {(job.settings.get('HDD_1') or job.settings['ISO_1'])}
"""
            )
        return res


def main() -> None:
    from argparse import ArgumentParser
    from json import loads

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

    if args.print_state:
        print(running_build.as_markdown(args.failed_only))

    if args.cancel:
        running_build.cancel_all_jobs()

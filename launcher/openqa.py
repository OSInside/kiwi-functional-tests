from typing import Literal
from openqa_client.client import OpenQA_Client
from pydantic import BaseModel, ConfigDict


def _to_job_dep_key(key: str) -> str:
    if key == "directly_chained":
        return "Directly chained"
    return key.capitalize()


class JobDependency(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=_to_job_dep_key
    )

    #: jobs launched after this test
    chained: list[int]
    #: jobs running in parallel
    parallel: list[int]
    directly_chained: list[int]


class Job(BaseModel):
    """A test job on openQA"""

    #: assets that belong to this job
    assets: dict[str, list[str]] | None = None
    assigned_worker_id: int | None = None
    blocked_by_id: int | None
    children: JobDependency
    group: str | None = None
    #: id of the job as which this failed job has been cloned
    clone_id: int | None = None
    #: original job if this one is a clone
    origin_id: int | None = None
    id: int
    #: full name of this test
    name: str
    #: numerical priority (the lower, the more the job will be preferred)
    priority: int
    has_parents: Literal[1, 0]
    group_id: int | None
    parents: JobDependency
    parents_ok: Literal[1, 0, ""]
    result: Literal[
        "scheduled",
        "softfailed",
        "user_cancelled",
        "failed",
        "skipped",
        "incomplete",
        "passed",
        "none",
        "parallel_failed",
        "parallel_restarted",
        "user_restarted",
        "obsoleted",
        "timeout_exceeded",
    ]
    settings: dict[str, str]
    state: Literal["done", "cancelled", "scheduled", "running"]
    test: str
    #: timestamp when the test finished or failed
    t_finished: str | None
    #: Timestamp when the test was launched.
    #: This value can be none even if t_finished is set, e.g. if the test failed
    #: due to missing assets
    t_started: str | None


def fetch_job(client: OpenQA_Client, job_id: int) -> Job:
    return Job(**client.openqa_request("GET", f"jobs/{job_id}")["job"])


def restart_job(client: OpenQA_Client, job: int | Job) -> None:
    job_id = job if isinstance(job, int) else job.id
    client.openqa_request("POST", f"jobs/{job_id}/restart")


def main() -> None:
    import argparse
    from launcher.client import NoWaitClient
    from launcher.argparser import SERVER_PARSER

    parser = argparse.ArgumentParser(parents=[SERVER_PARSER])
    parser.add_argument("job_id", type=int, nargs=1)

    args = parser.parse_args()
    print(
        fetch_job(
            client=NoWaitClient(server=args.server[0], scheme=args.scheme[0]),
            job_id=args.job_id[0],
        )
    )

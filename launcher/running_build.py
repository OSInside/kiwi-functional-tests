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

    def fetch_job_states(self) -> dict[int, Job]:
        client = self._client
        job_results: dict[int, Job] = {}
        for job_id in self.job_ids:
            job_results[job_id] = fetch_job(client, job_id)
        return job_results

    def get_unfinished_jobs(self) -> list[int]:
        job_states = self.fetch_job_states()
        unfinished: list[int] = []

        for job_id in job_states:
            if job_states[job_id].state not in ("cancelled", "done"):
                unfinished.append(job_id)

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

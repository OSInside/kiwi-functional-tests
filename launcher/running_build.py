from dataclasses import dataclass
from typing import Dict, List

from launcher.client import NoWaitClient
from launcher.types import JobState


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
    scheme: str
    job_ids: List[int]

    def _get_client(self) -> NoWaitClient:
        return NoWaitClient(server=self.server, scheme=self.scheme)

    def get_job_states(self) -> Dict[int, JobState]:
        client = self._get_client()
        job_results: Dict[int, JobState] = {}
        for job_id in self.job_ids:
            job = client.openqa_request("GET", f"jobs/{job_id}")["job"]
            result, state = job.pop("state"), job.pop("result")
            job_results[job_id] = {
                **JobState(state=state, result=result),
                **job,
            }
        return job_results

    def get_unfinished_jobs(self) -> List[int]:
        job_states = self.get_job_states()
        unfinished: List[int] = []

        for job_id in job_states:
            if job_states[job_id]["state"] not in ("cancelled", "done"):
                unfinished.append(job_id)

        return unfinished

    def cancel_all_jobs(self) -> None:
        client = self._get_client()
        failures = []
        for job_id in self.job_ids:
            try:
                client.openqa_request("POST", f"jobs/{job_id}/cancel")
            except Exception as exc:
                failures.append(CancelFailure(job_id, exc))

        for failure in failures:
            print(failure)

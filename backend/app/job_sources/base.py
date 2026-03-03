from __future__ import annotations

from typing import Protocol

from ..models import JobPosting, JobSearchRequest


class JobSource(Protocol):
    provider_name: str

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        raise NotImplementedError

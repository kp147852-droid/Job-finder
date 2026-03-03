from __future__ import annotations

from typing import Protocol

from ..models import JobPosting, ResumeData, UserProfile
from .models import AdapterRunResult


class ApplicationAdapter(Protocol):
    provider_name: str

    def apply(
        self,
        *,
        user: UserProfile,
        resume: ResumeData,
        job: JobPosting,
        storage_state_path: str | None,
    ) -> AdapterRunResult:
        raise NotImplementedError

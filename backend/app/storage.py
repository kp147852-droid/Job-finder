from __future__ import annotations

from typing import Dict, List

from .models import ApplicationRecord, JobPosting, ResumeData, UserProfile


USERS: Dict[str, UserProfile] = {}
RESUMES: Dict[str, ResumeData] = {}
JOBS: Dict[str, JobPosting] = {}
APPLICATIONS: Dict[str, ApplicationRecord] = {}
VAULT_CREDENTIALS: Dict[tuple[str, str], str] = {}
AUTOMATION_TASKS: Dict[str, dict] = {}


def list_jobs() -> List[JobPosting]:
    return list(JOBS.values())

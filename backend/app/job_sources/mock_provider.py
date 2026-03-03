from __future__ import annotations

from uuid import uuid4

from ..models import JobPosting, JobSearchRequest, JobType


class MockJobSource:
    provider_name = "mock"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        location = request.location or "Remote"
        jobs = [
            JobPosting(
                job_id=str(uuid4()),
                source="mock",
                title="Data Analyst",
                company="Acme Analytics",
                location=location,
                is_remote=request.remote_only,
                salary_min=85000,
                salary_max=110000,
                job_type=JobType.FULL_TIME,
                required_skills=["python", "sql", "tableau"],
                description="Analyze business data and build dashboards.",
                apply_url="https://example.com/jobs/analyst",
            ),
            JobPosting(
                job_id=str(uuid4()),
                source="mock",
                title="Business Intelligence Analyst",
                company="Northwind",
                location=location,
                is_remote=request.remote_only,
                salary_min=90000,
                salary_max=120000,
                job_type=JobType.FULL_TIME,
                required_skills=["sql", "power bi", "excel"],
                description="Own BI reporting and stakeholder insights.",
                apply_url="https://example.com/jobs/bi-analyst",
            ),
        ]
        return jobs[: max(1, request.limit)]

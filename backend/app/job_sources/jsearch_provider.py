from __future__ import annotations

from uuid import uuid4

import httpx

from ..config import settings
from ..models import JobPosting, JobSearchRequest, JobType


class JSearchJobSource:
    provider_name = "jsearch"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        if not settings.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY is required for jsearch provider")

        query = request.query
        if request.location:
            query = f"{query} in {request.location}"
        if request.remote_only:
            query = f"{query} remote"

        headers = {
            "X-RapidAPI-Key": settings.rapidapi_key,
            "X-RapidAPI-Host": settings.rapidapi_host,
        }
        params = {"query": query, "num_pages": "1"}

        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                f"https://{settings.rapidapi_host}/search",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data", [])
        jobs: list[JobPosting] = []
        for item in data[: request.limit]:
            title = item.get("job_title") or "Unknown Title"
            company = item.get("employer_name") or "Unknown Company"
            location = item.get("job_city") or item.get("job_country") or "Unknown"
            is_remote = bool(item.get("job_is_remote"))
            description = item.get("job_description") or ""
            apply_url = item.get("job_apply_link") or item.get("job_google_link") or ""
            if not apply_url:
                continue

            jobs.append(
                JobPosting(
                    job_id=item.get("job_id") or str(uuid4()),
                    source="jsearch",
                    title=title,
                    company=company,
                    location=location,
                    is_remote=is_remote,
                    salary_min=item.get("job_min_salary"),
                    salary_max=item.get("job_max_salary"),
                    job_type=JobType.FULL_TIME,
                    required_skills=[],
                    description=description,
                    apply_url=apply_url,
                )
            )
        return jobs

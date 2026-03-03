from __future__ import annotations

from uuid import uuid4

import httpx

from ..models import JobPosting, JobSearchRequest, JobType


class PublicJobSource:
    provider_name = "public"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        # No API key required. Uses a public job board feed.
        endpoint = "https://www.arbeitnow.com/api/job-board-api"
        jobs: list[JobPosting] = []

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(endpoint)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return jobs

        data = payload.get("data", [])
        query_tokens = [token.lower() for token in request.query.split() if token.strip()]
        location_filter = (request.location or "").lower().strip()

        for item in data:
            title = (item.get("title") or "Unknown Title").strip()
            company = (item.get("company_name") or "Unknown Company").strip()
            location = (item.get("location") or "Unknown").strip()
            description = item.get("description") or ""
            apply_url = item.get("url") or ""
            if not apply_url:
                continue

            text = f"{title} {company} {description}".lower()
            if query_tokens and not all(token in text for token in query_tokens):
                continue

            is_remote = location.lower() in {"remote", "worldwide"}
            if request.remote_only and not is_remote:
                continue
            if location_filter and location_filter not in location.lower() and not is_remote:
                continue

            jobs.append(
                JobPosting(
                    job_id=item.get("slug") or str(uuid4()),
                    source="public",
                    title=title,
                    company=company,
                    location=location,
                    is_remote=is_remote,
                    salary_min=None,
                    salary_max=None,
                    job_type=JobType.FULL_TIME,
                    required_skills=[str(tag) for tag in (item.get("tags") or [])[:10]],
                    description=description,
                    apply_url=apply_url,
                )
            )

            if len(jobs) >= request.limit:
                break

        return jobs

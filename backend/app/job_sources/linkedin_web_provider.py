from __future__ import annotations

from urllib.parse import quote_plus
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from ..models import JobPosting, JobSearchRequest, JobType


class LinkedInWebJobSource:
    provider_name = "linkedin_web"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        query = quote_plus(request.query)
        location = quote_plus(request.location or "United States")
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        jobs: list[JobPosting] = []
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
        except Exception:
            return jobs

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("a[href*='/jobs/view/']")
        seen = set()
        for link in links:
            href = (link.get("href") or "").strip()
            if not href or href in seen:
                continue
            seen.add(href)

            title = " ".join(link.get_text(" ", strip=True).split()) or "LinkedIn Job"
            parent = link.find_parent()
            location = ""
            company = ""
            if parent:
                location_text = parent.get_text(" ", strip=True)
                location = location_text[:80]

            jobs.append(
                JobPosting(
                    job_id=str(uuid4()),
                    source="linkedin_web",
                    title=title,
                    company=company or "LinkedIn",
                    location=location or (request.location or "Unknown"),
                    is_remote="remote" in title.lower(),
                    salary_min=None,
                    salary_max=None,
                    job_type=JobType.FULL_TIME,
                    required_skills=[],
                    description="Discovered from LinkedIn web search.",
                    apply_url=href,
                )
            )
            if len(jobs) >= request.limit:
                break

        return jobs

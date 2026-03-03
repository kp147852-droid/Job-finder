from __future__ import annotations

from urllib.parse import quote_plus
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from ..models import JobPosting, JobSearchRequest, JobType


class IndeedWebJobSource:
    provider_name = "indeed_web"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        query = quote_plus(request.query)
        location = quote_plus(request.location or "")
        url = f"https://www.indeed.com/jobs?q={query}&l={location}"

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
        cards = soup.select("a[href*='/viewjob']")
        seen = set()
        for link in cards:
            href = (link.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.indeed.com{href}"
            if href in seen:
                continue
            seen.add(href)

            title = " ".join(link.get_text(" ", strip=True).split()) or "Indeed Job"
            jobs.append(
                JobPosting(
                    job_id=str(uuid4()),
                    source="indeed_web",
                    title=title,
                    company="Indeed",
                    location=request.location or "Unknown",
                    is_remote="remote" in title.lower(),
                    salary_min=None,
                    salary_max=None,
                    job_type=JobType.FULL_TIME,
                    required_skills=[],
                    description="Discovered from Indeed web search.",
                    apply_url=href,
                )
            )
            if len(jobs) >= request.limit:
                break

        return jobs

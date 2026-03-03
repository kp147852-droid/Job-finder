from __future__ import annotations

from urllib.parse import parse_qs, quote_plus, urlparse
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from ..models import JobPosting, JobSearchRequest, JobType


class GoogleWebJobSource:
    provider_name = "google_web"

    def search_jobs(self, request: JobSearchRequest) -> list[JobPosting]:
        query_text = f"{request.query} jobs {request.location or ''}".strip()
        query = quote_plus(query_text)
        url = f"https://www.google.com/search?q={query}"

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
        seen = set()
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href.startswith("/url?q="):
                continue

            parsed = urlparse(href)
            target = parse_qs(parsed.query).get("q", [""])[0]
            if not target:
                continue
            lower = target.lower()
            if "linkedin.com/jobs" not in lower and "indeed.com" not in lower:
                continue
            if target in seen:
                continue
            seen.add(target)

            title = " ".join(a.get_text(" ", strip=True).split()) or "Google-discovered Job"
            jobs.append(
                JobPosting(
                    job_id=str(uuid4()),
                    source="google_web",
                    title=title,
                    company="Google Result",
                    location=request.location or "Unknown",
                    is_remote="remote" in title.lower(),
                    salary_min=None,
                    salary_max=None,
                    job_type=JobType.FULL_TIME,
                    required_skills=[],
                    description="Discovered from Google web results.",
                    apply_url=target,
                )
            )
            if len(jobs) >= request.limit:
                break

        return jobs

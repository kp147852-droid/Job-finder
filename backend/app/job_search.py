from __future__ import annotations

from .config import settings
from .job_sources.google_web_provider import GoogleWebJobSource
from .job_sources.indeed_web_provider import IndeedWebJobSource
from .job_sources.jsearch_provider import JSearchJobSource
from .job_sources.linkedin_web_provider import LinkedInWebJobSource
from .job_sources.mock_provider import MockJobSource
from .job_sources.public_provider import PublicJobSource
from .models import JobPosting, JobSearchRequest


class JobSourceRegistry:
    def __init__(self) -> None:
        self._providers = {
            "public": PublicJobSource(),
            "mock": MockJobSource(),
            "jsearch": JSearchJobSource(),
            "linkedin_web": LinkedInWebJobSource(),
            "indeed_web": IndeedWebJobSource(),
            "google_web": GoogleWebJobSource(),
        }

    def active_provider_name(self) -> str:
        return settings.job_provider if settings.job_provider in self._providers else "public"

    def search(self, request: JobSearchRequest) -> tuple[str, list[JobPosting]]:
        provider_name = self.active_provider_name()
        provider = self._providers[provider_name]
        jobs = provider.search_jobs(request)
        return provider_name, jobs

    def search_selected(self, request: JobSearchRequest, providers: list[str]) -> tuple[str, list[JobPosting]]:
        selected = [item.strip().lower() for item in providers if item.strip()]
        if not selected:
            return self.search(request)

        jobs: list[JobPosting] = []
        used = []
        for provider_name in selected:
            provider = self._providers.get(provider_name)
            if not provider:
                continue
            used.append(provider_name)
            try:
                jobs.extend(provider.search_jobs(request))
            except Exception:
                continue
        return "+".join(used) if used else self.active_provider_name(), jobs


registry = JobSourceRegistry()

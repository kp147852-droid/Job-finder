from __future__ import annotations

import os


class Settings:
    job_provider: str = os.getenv("JOB_PROVIDER", "public").lower()
    rapidapi_key: str | None = os.getenv("RAPIDAPI_KEY")
    rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    playwright_headless: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"


settings = Settings()

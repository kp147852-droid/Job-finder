from app.job_search import registry
from app.config import settings
from app.models import JobSearchRequest


def test_mock_job_search_discovers_jobs():
    settings.job_provider = "mock"
    request = JobSearchRequest(
        user_id="u1",
        query="data analyst",
        location="Chicago, IL",
        remote_only=False,
        limit=5,
    )
    provider, jobs = registry.search(request)
    assert provider == "mock"
    assert len(jobs) >= 1
    assert all(job.apply_url for job in jobs)

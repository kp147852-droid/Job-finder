from app.apply_service import apply_with_browser_adapter
from app.models import JobPosting, JobType, ResumeData, UserProfile


class StubResult:
    def __init__(self, success, needs_user_input=False, missing_field=None, prompt=None, details=None):
        self.success = success
        self.needs_user_input = needs_user_input
        self.missing_field = missing_field
        self.prompt = prompt
        self.details = details


class StubAdapter:
    def __init__(self, result):
        self._result = result

    def apply(self, *, user, resume, job, storage_state_path):
        return self._result


def _sample_user_resume_job():
    user = UserProfile(
        user_id="u1",
        full_name="Test User",
        email="test@example.com",
        locations=["Chicago"],
        target_titles=["Data Analyst"],
        remote_ok=True,
    )
    resume = ResumeData(
        user_id="u1",
        skills=["Python", "SQL"],
        titles=["Data Analyst"],
        years_experience=4,
        raw_text="4 years python sql",
    )
    job = JobPosting(
        job_id="j1",
        source="mock",
        title="Data Analyst",
        company="Acme",
        location="Chicago, IL",
        is_remote=False,
        salary_min=80000,
        salary_max=100000,
        job_type=JobType.FULL_TIME,
        required_skills=["python", "sql"],
        description="Analyze data",
        apply_url="https://example.com/apply",
    )
    return user, resume, job


def test_apply_service_submitted(monkeypatch):
    user, resume, job = _sample_user_resume_job()
    monkeypatch.setattr(
        "app.apply_service.get_adapter",
        lambda provider: StubAdapter(StubResult(success=True, details="ok")),
    )

    record = apply_with_browser_adapter(
        user=user,
        resume=resume,
        job=job,
        provider="linkedin",
        storage_state_path=None,
    )

    assert record.status.value == "submitted"
    assert record.issue is None


def test_apply_service_needs_user_input(monkeypatch):
    user, resume, job = _sample_user_resume_job()
    monkeypatch.setattr(
        "app.apply_service.get_adapter",
        lambda provider: StubAdapter(
            StubResult(
                success=False,
                needs_user_input=True,
                missing_field="captcha",
                prompt="Solve captcha",
            )
        ),
    )

    record = apply_with_browser_adapter(
        user=user,
        resume=resume,
        job=job,
        provider="indeed",
        storage_state_path=None,
    )

    assert record.status.value == "needs_user_input"
    assert record.issue is not None
    assert record.issue.field_name == "captcha"

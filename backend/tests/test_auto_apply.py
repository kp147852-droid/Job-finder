from app.automation import run_auto_apply
from app.models import AutoApplyRequest, JobPosting, JobType, ResumeData, UserProfile


def test_auto_apply_uses_threshold_and_creates_applications():
    user = UserProfile(
        user_id="u1",
        full_name="Taylor Tester",
        email="taylor@example.com",
        locations=["Chicago"],
        target_titles=["Data Analyst"],
        required_salary_min=80000,
        allowed_job_types=[JobType.FULL_TIME],
        remote_ok=True,
    )
    resume = ResumeData(
        user_id="u1",
        skills=["Python", "SQL", "Excel"],
        titles=["Data Analyst"],
        years_experience=4,
        raw_text="4 years Python SQL Excel",
    )

    jobs = [
        JobPosting(
            job_id="j1",
            source="indeed",
            title="Data Analyst",
            company="Acme",
            location="Chicago, IL",
            is_remote=False,
            salary_min=90000,
            job_type=JobType.FULL_TIME,
            required_skills=["python", "sql", "excel"],
            description="Standard role",
            apply_url="https://example.com/j1",
        ),
        JobPosting(
            job_id="j2",
            source="linkedin",
            title="Data Analyst",
            company="Beta",
            location="Remote",
            is_remote=True,
            salary_min=85000,
            job_type=JobType.FULL_TIME,
            required_skills=["python", "sql", "excel"],
            description="Requires clearance",
            apply_url="https://example.com/j2",
        ),
        JobPosting(
            job_id="j3",
            source="glassdoor",
            title="Warehouse Associate",
            company="Gamma",
            location="Chicago, IL",
            is_remote=False,
            salary_min=40000,
            job_type=JobType.FULL_TIME,
            required_skills=["forklift"],
            description="Not a match",
            apply_url="https://example.com/j3",
        ),
    ]

    result, records = run_auto_apply(
        user=user,
        resume=resume,
        jobs=jobs,
        request=AutoApplyRequest(user_id="u1", min_match_score=65, max_jobs=10),
    )

    assert result.searched_jobs == 3
    assert result.qualified_jobs == 2
    assert result.submitted == 1
    assert result.needs_user_input == 1
    assert len(records) == 2

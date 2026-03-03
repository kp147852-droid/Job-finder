from app.ai_matcher import assess_qualification
from app.models import JobPosting, JobType, ResumeData, UserProfile


def test_assess_qualification_returns_score_and_reasons():
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
        skills=["Python", "SQL", "Tableau"],
        titles=["Data Analyst"],
        years_experience=3,
        raw_text="3 years python sql tableau",
    )
    job = JobPosting(
        job_id="j1",
        source="mock",
        title="Data Analyst",
        company="Acme",
        location="Chicago, IL",
        is_remote=False,
        salary_min=85000,
        salary_max=100000,
        job_type=JobType.FULL_TIME,
        required_skills=["python", "sql", "excel"],
        description="Analyze datasets and provide reporting.",
        apply_url="https://example.com/apply",
    )

    result = assess_qualification(user, resume, job)
    assert 0 <= result.score <= 100
    assert result.job_id == "j1"

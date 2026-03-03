from app.matching import score_job
from app.models import JobPosting, JobType, ResumeData, UserProfile


def test_score_job_skill_overlap_and_preferences():
    user = UserProfile(
        user_id="u1",
        full_name="Test User",
        email="test@example.com",
        locations=["Austin"],
        target_titles=["Data Analyst"],
        required_salary_min=70000,
        allowed_job_types=[JobType.FULL_TIME],
        remote_ok=True,
    )
    resume = ResumeData(
        user_id="u1",
        skills=["Python", "SQL", "Tableau"],
        titles=["Data Analyst"],
        years_experience=3,
        raw_text="3 years Python SQL Tableau",
    )
    job = JobPosting(
        job_id="j1",
        source="indeed",
        title="Data Analyst",
        company="Acme",
        location="Austin, TX",
        is_remote=False,
        salary_min=90000,
        job_type=JobType.FULL_TIME,
        required_skills=["python", "sql", "excel"],
        description="Analytics role",
        apply_url="https://example.com/apply",
    )

    result = score_job(user, resume, job)
    assert result.score > 0
    assert result.job_id == "j1"
    assert any("Title preference matched" in reason for reason in result.reasons)

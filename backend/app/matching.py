from __future__ import annotations

from .models import JobPosting, MatchResult, ResumeData, UserProfile


def score_job(user: UserProfile, resume: ResumeData, job: JobPosting) -> MatchResult:
    score = 0.0
    reasons: list[str] = []

    resume_skills = {s.lower() for s in resume.skills}
    required_skills = {s.lower() for s in job.required_skills}
    overlap = resume_skills.intersection(required_skills)

    if required_skills:
        skill_score = (len(overlap) / len(required_skills)) * 50
        score += skill_score
    else:
        score += 10

    if overlap:
        reasons.append(f"Skill overlap: {', '.join(sorted(overlap))}")

    if job.is_remote and user.remote_ok:
        score += 15
        reasons.append("Remote preference matched")
    elif any(loc.lower() in job.location.lower() for loc in user.locations):
        score += 15
        reasons.append("Location matched")

    if any(title.lower() in job.title.lower() for title in user.target_titles):
        score += 20
        reasons.append("Title preference matched")

    if user.required_salary_min is not None and job.salary_min is not None:
        if job.salary_min >= user.required_salary_min:
            score += 10
            reasons.append("Salary target met")
        else:
            score -= 10
            reasons.append("Salary below preferred minimum")

    score = max(0.0, min(score, 100.0))
    return MatchResult(user_id=user.user_id, job_id=job.job_id, score=score, reasons=reasons)

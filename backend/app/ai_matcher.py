from __future__ import annotations

import json
from typing import Any

from .config import settings
from .models import JobPosting, QualificationAssessment, ResumeData, UserProfile

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


def _heuristic_assessment(user: UserProfile, resume: ResumeData, job: JobPosting) -> QualificationAssessment:
    resume_skills = {skill.lower() for skill in resume.skills}
    required_skills = {skill.lower() for skill in job.required_skills}

    overlap = sorted(resume_skills.intersection(required_skills))
    missing = sorted(required_skills - resume_skills)

    score = 40.0
    if required_skills:
        score += (len(overlap) / len(required_skills)) * 40.0
    else:
        score += 10.0

    title_match = any(t.lower() in job.title.lower() for t in user.target_titles)
    if title_match:
        score += 10.0

    location_match = job.is_remote and user.remote_ok
    if not location_match and user.locations:
        location_match = any(loc.lower() in job.location.lower() for loc in user.locations)
    if location_match:
        score += 10.0

    score = max(0.0, min(score, 100.0))

    reasons = []
    if overlap:
        reasons.append(f"Skill overlap: {', '.join(overlap)}")
    if title_match:
        reasons.append("Target title alignment")
    if location_match:
        reasons.append("Location or remote preference alignment")

    return QualificationAssessment(
        user_id=user.user_id,
        job_id=job.job_id,
        score=score,
        reasons=reasons,
        missing_requirements=missing,
    )


def _llm_assessment(user: UserProfile, resume: ResumeData, job: JobPosting) -> QualificationAssessment:
    if OpenAI is None or not settings.openai_api_key:
        return _heuristic_assessment(user, resume, job)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = {
        "user": {
            "target_titles": user.target_titles,
            "locations": user.locations,
            "remote_ok": user.remote_ok,
            "required_salary_min": user.required_salary_min,
        },
        "resume": {
            "skills": resume.skills,
            "titles": resume.titles,
            "years_experience": resume.years_experience,
            "education": resume.education,
            "raw_text": resume.raw_text[:4000],
        },
        "job": {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "is_remote": job.is_remote,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "required_skills": job.required_skills,
            "description": job.description[:6000],
        },
        "task": "Score job fit from 0-100 and return concise reasons and missing requirements.",
        "output_schema": {
            "score": "number 0-100",
            "reasons": ["string"],
            "missing_requirements": ["string"],
        },
    }

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": "You evaluate resume-job fit objectively. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": json.dumps(prompt),
            },
        ],
    )

    text = getattr(response, "output_text", "")
    if not text:
        return _heuristic_assessment(user, resume, job)

    try:
        parsed: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError:
        return _heuristic_assessment(user, resume, job)

    score = float(parsed.get("score", 0.0))
    reasons = [str(item) for item in parsed.get("reasons", [])][:6]
    missing = [str(item) for item in parsed.get("missing_requirements", [])][:8]

    return QualificationAssessment(
        user_id=user.user_id,
        job_id=job.job_id,
        score=max(0.0, min(score, 100.0)),
        reasons=reasons,
        missing_requirements=missing,
    )


def assess_qualification(user: UserProfile, resume: ResumeData, job: JobPosting) -> QualificationAssessment:
    return _llm_assessment(user, resume, job)

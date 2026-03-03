from __future__ import annotations

from .matching import score_job
from .models import (
    ApplicationRecord,
    ApplicationStatus,
    AutoApplyRequest,
    AutoApplyResult,
    QualificationAssessment,
    JobPosting,
    ResumeData,
    UserProfile,
)
from .orchestrator import start_application


def run_auto_apply(
    *,
    user: UserProfile,
    resume: ResumeData,
    jobs: list[JobPosting],
    request: AutoApplyRequest,
):
    ranked = [score_job(user, resume, job) for job in jobs]
    ranked.sort(key=lambda match: match.score, reverse=True)

    limited = ranked[: request.max_jobs]
    qualified = [match for match in limited if match.score >= request.min_match_score]

    records = []
    submitted = 0
    needs_user_input = 0

    for match in qualified:
        job = next((item for item in jobs if item.job_id == match.job_id), None)
        if not job:
            continue
        record = start_application(user=user, resume=resume, job=job)
        records.append(record)
        if record.status == ApplicationStatus.SUBMITTED:
            submitted += 1
        elif record.status == ApplicationStatus.NEEDS_USER_INPUT:
            needs_user_input += 1

    result = AutoApplyResult(
        user_id=user.user_id,
        searched_jobs=len(jobs),
        qualified_jobs=len(qualified),
        submitted=submitted,
        needs_user_input=needs_user_input,
        skipped=max(0, len(limited) - len(qualified)),
        application_ids=[record.application_id for record in records],
    )
    return result, records


def run_auto_apply_from_assessments(
    *,
    user: UserProfile,
    resume: ResumeData,
    jobs: list[JobPosting],
    assessments: list[QualificationAssessment],
    min_ai_score: float,
    max_apply: int,
) -> tuple[list[ApplicationRecord], int, int]:
    job_map = {job.job_id: job for job in jobs}
    ranked = sorted(assessments, key=lambda item: item.score, reverse=True)
    qualified = [item for item in ranked if item.score >= min_ai_score][:max_apply]

    records: list[ApplicationRecord] = []
    submitted = 0
    needs_user_input = 0
    for assessment in qualified:
        job = job_map.get(assessment.job_id)
        if not job:
            continue
        record = start_application(user=user, resume=resume, job=job)
        records.append(record)
        if record.status == ApplicationStatus.SUBMITTED:
            submitted += 1
        elif record.status == ApplicationStatus.NEEDS_USER_INPUT:
            needs_user_input += 1
    return records, submitted, needs_user_input

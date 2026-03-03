from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .models import (
    ApplicationIssue,
    ApplicationRecord,
    ApplicationStatus,
    JobPosting,
    ResumeData,
    UserProfile,
)


REQUIRED_PROFILE_FIELDS = ("full_name", "email")


def _missing_profile_field(user: UserProfile) -> str | None:
    for field_name in REQUIRED_PROFILE_FIELDS:
        if not getattr(user, field_name, None):
            return field_name
    return None


def _missing_resume_field(resume: ResumeData) -> str | None:
    if not resume.skills:
        return "skills"
    if not resume.raw_text.strip():
        return "raw_text"
    return None


def start_application(user: UserProfile, resume: ResumeData, job: JobPosting) -> ApplicationRecord:
    now = datetime.utcnow()

    missing_profile = _missing_profile_field(user)
    if missing_profile:
        return ApplicationRecord(
            application_id=str(uuid4()),
            user_id=user.user_id,
            job_id=job.job_id,
            status=ApplicationStatus.NEEDS_USER_INPUT,
            created_at=now,
            updated_at=now,
            issue=ApplicationIssue(
                field_name=missing_profile,
                reason="Required profile data missing",
                prompt=f"Please provide your {missing_profile.replace('_', ' ')} to continue.",
            ),
            notes=["Blocked before submit due to missing profile data."],
        )

    missing_resume = _missing_resume_field(resume)
    if missing_resume:
        return ApplicationRecord(
            application_id=str(uuid4()),
            user_id=user.user_id,
            job_id=job.job_id,
            status=ApplicationStatus.NEEDS_USER_INPUT,
            created_at=now,
            updated_at=now,
            issue=ApplicationIssue(
                field_name=missing_resume,
                reason="Resume is missing required information",
                prompt="Your resume is missing key info. Add the missing data and retry.",
            ),
            notes=["Blocked before submit due to incomplete resume parsing."],
        )

    # Placeholder: in a production system, this is where a site adapter executes form filling.
    if "clearance" in job.description.lower() and "clearance" not in {s.lower() for s in resume.skills}:
        return ApplicationRecord(
            application_id=str(uuid4()),
            user_id=user.user_id,
            job_id=job.job_id,
            status=ApplicationStatus.NEEDS_USER_INPUT,
            created_at=now,
            updated_at=now,
            issue=ApplicationIssue(
                field_name="clearance_status",
                reason="Employer form requires clearance verification",
                prompt="This application needs your clearance status. Please provide it to continue.",
            ),
            notes=["Automation paused for human input on employer-specific field."],
        )

    return ApplicationRecord(
        application_id=str(uuid4()),
        user_id=user.user_id,
        job_id=job.job_id,
        status=ApplicationStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
        notes=["Application submitted by automation adapter."],
    )

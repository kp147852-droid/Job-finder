from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .adapters.factory import get_adapter
from .models import (
    ApplicationIssue,
    ApplicationRecord,
    ApplicationStatus,
    JobPosting,
    ResumeData,
    UserProfile,
)


def apply_with_browser_adapter(
    *,
    user: UserProfile,
    resume: ResumeData,
    job: JobPosting,
    provider: str,
    storage_state_path: str | None,
) -> ApplicationRecord:
    now = datetime.utcnow()
    adapter = get_adapter(provider)
    result = adapter.apply(user=user, resume=resume, job=job, storage_state_path=storage_state_path)

    status = ApplicationStatus.SUBMITTED if result.success else ApplicationStatus.FAILED
    issue = None
    notes = [f"Adapter provider: {provider}"]

    if result.needs_user_input:
        status = ApplicationStatus.NEEDS_USER_INPUT
        issue = ApplicationIssue(
            field_name=result.missing_field or "manual_review",
            reason="Browser automation requires user action",
            prompt=result.prompt or "Please continue manually and retry.",
        )

    if result.details:
        notes.append(result.details)

    return ApplicationRecord(
        application_id=str(uuid4()),
        user_id=user.user_id,
        job_id=job.job_id,
        status=status,
        created_at=now,
        updated_at=now,
        issue=issue,
        notes=notes,
    )

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class UserProfile(BaseModel):
    user_id: str
    full_name: str
    email: str
    locations: List[str] = Field(default_factory=list)
    target_titles: List[str] = Field(default_factory=list)
    required_salary_min: Optional[int] = None
    allowed_job_types: List[JobType] = Field(default_factory=list)
    remote_ok: bool = True


class ResumeData(BaseModel):
    user_id: str
    skills: List[str] = Field(default_factory=list)
    titles: List[str] = Field(default_factory=list)
    years_experience: float = 0.0
    education: List[str] = Field(default_factory=list)
    raw_text: str = ""


class JobPosting(BaseModel):
    job_id: str
    source: str
    title: str
    company: str
    location: str
    is_remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: JobType = JobType.FULL_TIME
    required_skills: List[str] = Field(default_factory=list)
    description: str = ""
    apply_url: str


class MatchResult(BaseModel):
    user_id: str
    job_id: str
    score: float
    reasons: List[str] = Field(default_factory=list)


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    NEEDS_USER_INPUT = "needs_user_input"
    SUBMITTED = "submitted"
    FAILED = "failed"


class ApplicationIssue(BaseModel):
    field_name: str
    reason: str
    prompt: str


class ApplicationRecord(BaseModel):
    application_id: str
    user_id: str
    job_id: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    issue: Optional[ApplicationIssue] = None
    notes: List[str] = Field(default_factory=list)


class StartApplicationRequest(BaseModel):
    user_id: str
    job_id: str


class ResolveIssueRequest(BaseModel):
    application_id: str
    value: str


class AutoApplyRequest(BaseModel):
    user_id: str
    min_match_score: float = 65.0
    max_jobs: int = 25


class AutoApplyResult(BaseModel):
    user_id: str
    searched_jobs: int
    qualified_jobs: int
    submitted: int
    needs_user_input: int
    skipped: int
    application_ids: List[str] = Field(default_factory=list)


class JobSearchRequest(BaseModel):
    user_id: str
    query: str
    location: Optional[str] = None
    remote_only: bool = False
    limit: int = 25


class QualificationAssessment(BaseModel):
    user_id: str
    job_id: str
    score: float
    reasons: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)


class DiscoveredJobsResult(BaseModel):
    provider: str
    count: int
    job_ids: List[str] = Field(default_factory=list)


class DiscoverAndAutoApplyRequest(BaseModel):
    user_id: str
    query: str
    search_sources: List[str] = Field(
        default_factory=lambda: ["public", "linkedin_web", "indeed_web", "google_web"]
    )
    additional_queries: List[str] = Field(default_factory=list)
    focus_fields: List[str] = Field(default_factory=list)
    education_levels: List[str] = Field(default_factory=list)
    include_titles: List[str] = Field(default_factory=list)
    exclude_titles: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    remote_only: bool = False
    limit: int = 25
    min_ai_score: float = 70.0
    max_apply: int = 15


class DiscoverAndAutoApplyResult(BaseModel):
    user_id: str
    provider: str
    discovered_jobs: int
    qualified_jobs: int
    submitted: int
    needs_user_input: int
    application_ids: List[str] = Field(default_factory=list)
    assessments: List[QualificationAssessment] = Field(default_factory=list)


class BrowserApplyRequest(BaseModel):
    user_id: str
    job_id: str
    provider: str
    storage_state_path: Optional[str] = None


class VaultCredentialRequest(BaseModel):
    user_id: str
    provider: str
    username: Optional[str] = None
    token: Optional[str] = None
    password: Optional[str] = None


class VaultCredentialMeta(BaseModel):
    user_id: str
    provider: str
    stored: bool


class AsyncTaskResponse(BaseModel):
    task_id: str
    status: str


class SpecificAutoApplyRequest(BaseModel):
    user_id: str
    job_ids: List[str] = Field(default_factory=list)
    min_ai_score: float = 60.0
    max_apply: int = 25

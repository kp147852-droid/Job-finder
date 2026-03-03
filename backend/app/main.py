from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .ai_matcher import assess_qualification
from .apply_service import apply_with_browser_adapter
from .automation import run_auto_apply, run_auto_apply_from_assessments
from .job_search import registry
from .matching import score_job
from .models import (
    ApplicationRecord,
    ApplicationStatus,
    AsyncTaskResponse,
    AutoApplyRequest,
    AutoApplyResult,
    BrowserApplyRequest,
    DiscoverAndAutoApplyRequest,
    DiscoverAndAutoApplyResult,
    DiscoveredJobsResult,
    JobPosting,
    JobSearchRequest,
    MatchResult,
    ResolveIssueRequest,
    SpecificAutoApplyRequest,
    StartApplicationRequest,
    UserProfile,
    VaultCredentialMeta,
    VaultCredentialRequest,
)
from .orchestrator import start_application
from .resume_parser import parse_resume_text
from .storage import APPLICATIONS, AUTOMATION_TASKS, JOBS, RESUMES, USERS, VAULT_CREDENTIALS
from .task_queue import enqueue
from .vault import has_credential, save_credential


class ResumeUploadRequest(BaseModel):
    user_id: str
    resume_text: str


app = FastAPI(title="Job Apply Assistant API", version="0.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

FIELD_KEYWORDS = {
    "it": ("it", "information technology", "sysadmin", "network", "help desk", "developer"),
    "education": ("education", "teacher", "curriculum", "instructional", "school", "academic"),
    "business": ("business", "operations", "analyst", "strategy", "management"),
    "healthcare": ("healthcare", "clinic", "hospital", "medical"),
    "finance": ("finance", "accounting", "financial", "banking"),
}
EDUCATION_KEYWORDS = {
    "high school": ("high school", "ged"),
    "associate": ("associate", "a.a.", "a.s."),
    "bachelor": ("bachelor", "b.s.", "b.a.", "undergraduate"),
    "master": ("master", "m.s.", "m.a.", "mba", "graduate"),
    "doctorate": ("phd", "doctorate", "doctoral"),
}


def _normalize(values: List[str]) -> List[str]:
    return [value.strip().lower() for value in values if value and value.strip()]


def _build_queries(payload: DiscoverAndAutoApplyRequest) -> List[str]:
    base_queries = [payload.query] + payload.additional_queries
    field_queries = []
    for field in _normalize(payload.focus_fields):
        field_queries.append(f"{payload.query} {field}")
    combined = [query.strip() for query in (base_queries + field_queries) if query.strip()]
    deduped = []
    seen = set()
    for query in combined:
        key = query.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(query)
    return deduped or [payload.query]


def _job_matches_filters(job: JobPosting, payload: DiscoverAndAutoApplyRequest) -> bool:
    text = f"{job.title} {job.company} {job.description}".lower()

    include_titles = _normalize(payload.include_titles)
    if include_titles and not any(title in job.title.lower() for title in include_titles):
        return False

    exclude_titles = _normalize(payload.exclude_titles)
    if exclude_titles and any(title in job.title.lower() for title in exclude_titles):
        return False

    focus_fields = _normalize(payload.focus_fields)
    if focus_fields:
        found_field = False
        for field in focus_fields:
            keywords = FIELD_KEYWORDS.get(field, (field,))
            if any(keyword in text for keyword in keywords):
                found_field = True
                break
        if not found_field:
            return False

    education_levels = _normalize(payload.education_levels)
    if education_levels:
        found_level = False
        for level in education_levels:
            keywords = EDUCATION_KEYWORDS.get(level, (level,))
            if any(keyword in text for keyword in keywords):
                found_level = True
                break
        if not found_level:
            return False

    return True


def _dedupe_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    deduped = []
    seen = set()
    for job in jobs:
        key = (job.apply_url.strip().lower(), job.title.strip().lower(), job.company.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped


def _run_discover_and_auto_apply(payload: DiscoverAndAutoApplyRequest) -> DiscoverAndAutoApplyResult:
    user = USERS.get(payload.user_id)
    resume = RESUMES.get(payload.user_id)
    if not user or not resume:
        raise HTTPException(status_code=404, detail="User or resume not found")

    queries = _build_queries(payload)
    provider = "unknown"
    jobs: List[JobPosting] = []
    per_query_limit = max(5, payload.limit // max(1, len(queries)))
    for query in queries:
        provider, found = registry.search_selected(
            JobSearchRequest(
                user_id=payload.user_id,
                query=query,
                location=payload.location,
                remote_only=payload.remote_only,
                limit=per_query_limit,
            ),
            providers=payload.search_sources,
        )
        jobs.extend(found)

    jobs = _dedupe_jobs(jobs)
    jobs = [job for job in jobs if _job_matches_filters(job, payload)]
    jobs = jobs[: payload.limit]

    for job in jobs:
        JOBS[job.job_id] = job

    assessments = [assess_qualification(user, resume, job) for job in jobs]
    records, submitted, needs_user_input = run_auto_apply_from_assessments(
        user=user,
        resume=resume,
        jobs=jobs,
        assessments=assessments,
        min_ai_score=payload.min_ai_score,
        max_apply=payload.max_apply,
    )

    for record in records:
        APPLICATIONS[record.application_id] = record

    qualified_jobs = len([assessment for assessment in assessments if assessment.score >= payload.min_ai_score])
    return DiscoverAndAutoApplyResult(
        user_id=payload.user_id,
        provider=provider,
        discovered_jobs=len(jobs),
        qualified_jobs=min(qualified_jobs, payload.max_apply),
        submitted=submitted,
        needs_user_input=needs_user_input,
        application_ids=[record.application_id for record in records],
        assessments=sorted(assessments, key=lambda item: item.score, reverse=True),
    )


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-single-user"}


@app.post("/vault/credentials", response_model=VaultCredentialMeta)
def save_vault_credential(payload: VaultCredentialRequest) -> VaultCredentialMeta:
    save_credential(
        user_id=payload.user_id,
        provider=payload.provider,
        data={
            "username": payload.username,
            "token": payload.token,
            "password": payload.password,
        },
    )
    return VaultCredentialMeta(user_id=payload.user_id, provider=payload.provider, stored=True)


@app.get("/vault/credentials/{user_id}", response_model=List[VaultCredentialMeta])
def list_vault_credentials(user_id: str) -> List[VaultCredentialMeta]:
    providers = sorted([provider for uid, provider in VAULT_CREDENTIALS if uid == user_id])
    return [
        VaultCredentialMeta(user_id=user_id, provider=provider, stored=has_credential(user_id, provider))
        for provider in providers
    ]


@app.post("/users", response_model=UserProfile)
def upsert_user(user: UserProfile) -> UserProfile:
    USERS[user.user_id] = user
    return user


@app.post("/resume")
def upload_resume(payload: ResumeUploadRequest):
    if payload.user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    parsed = parse_resume_text(user_id=payload.user_id, text=payload.resume_text)
    RESUMES[payload.user_id] = parsed
    return parsed


@app.post("/jobs", response_model=JobPosting)
def upsert_job(job: JobPosting) -> JobPosting:
    JOBS[job.job_id] = job
    return job


@app.get("/jobs", response_model=List[JobPosting])
def list_jobs() -> List[JobPosting]:
    return list(JOBS.values())


@app.get("/match/{user_id}", response_model=List[MatchResult])
def match_jobs(user_id: str) -> List[MatchResult]:
    user = USERS.get(user_id)
    resume = RESUMES.get(user_id)
    if not user or not resume:
        raise HTTPException(status_code=404, detail="User or resume not found")

    matches = [score_job(user, resume, job) for job in JOBS.values()]
    matches.sort(key=lambda x: x.score, reverse=True)
    return matches


@app.post("/applications/start", response_model=ApplicationRecord)
def start_application_endpoint(payload: StartApplicationRequest) -> ApplicationRecord:
    user = USERS.get(payload.user_id)
    resume = RESUMES.get(payload.user_id)
    job = JOBS.get(payload.job_id)
    if not user or not resume or not job:
        raise HTTPException(status_code=404, detail="User, resume, or job not found")

    record = start_application(user=user, resume=resume, job=job)
    APPLICATIONS[record.application_id] = record
    return record


@app.post("/applications/resolve", response_model=ApplicationRecord)
def resolve_application_issue(payload: ResolveIssueRequest) -> ApplicationRecord:
    record = APPLICATIONS.get(payload.application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")

    if record.status != ApplicationStatus.NEEDS_USER_INPUT or not record.issue:
        raise HTTPException(status_code=400, detail="Application is not waiting on user input")

    record.notes.append(
        f"User provided value for {record.issue.field_name} at {datetime.utcnow().isoformat()}"
    )
    record.issue = None
    record.status = ApplicationStatus.IN_PROGRESS
    record.updated_at = datetime.utcnow()

    record.status = ApplicationStatus.SUBMITTED
    record.notes.append("Application resumed and submitted.")
    record.updated_at = datetime.utcnow()

    APPLICATIONS[record.application_id] = record
    return record


@app.get("/applications", response_model=List[ApplicationRecord])
def list_applications() -> List[ApplicationRecord]:
    return list(APPLICATIONS.values())


@app.post("/automation/auto-apply", response_model=AutoApplyResult)
def auto_apply(payload: AutoApplyRequest) -> AutoApplyResult:
    user = USERS.get(payload.user_id)
    resume = RESUMES.get(payload.user_id)
    if not user or not resume:
        raise HTTPException(status_code=404, detail="User or resume not found")

    result, records = run_auto_apply(
        user=user,
        resume=resume,
        jobs=list(JOBS.values()),
        request=payload,
    )
    for record in records:
        APPLICATIONS[record.application_id] = record
    return result


@app.post("/jobs/discover", response_model=DiscoveredJobsResult)
def discover_jobs(payload: JobSearchRequest) -> DiscoveredJobsResult:
    if payload.user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")

    provider, jobs = registry.search(payload)
    for job in jobs:
        JOBS[job.job_id] = job

    return DiscoveredJobsResult(
        provider=provider,
        count=len(jobs),
        job_ids=[job.job_id for job in jobs],
    )


@app.post("/automation/discover-and-auto-apply", response_model=DiscoverAndAutoApplyResult)
def discover_and_auto_apply(payload: DiscoverAndAutoApplyRequest) -> DiscoverAndAutoApplyResult:
    return _run_discover_and_auto_apply(payload)


@app.post("/automation/discover-and-auto-apply/async", response_model=AsyncTaskResponse)
def discover_and_auto_apply_async(payload: DiscoverAndAutoApplyRequest) -> AsyncTaskResponse:
    task_id = enqueue(lambda p: _run_discover_and_auto_apply(p).model_dump(), payload)
    return AsyncTaskResponse(task_id=task_id, status="queued")


@app.post("/automation/auto-apply-specific", response_model=DiscoverAndAutoApplyResult)
def auto_apply_specific(payload: SpecificAutoApplyRequest) -> DiscoverAndAutoApplyResult:
    user = USERS.get(payload.user_id)
    resume = RESUMES.get(payload.user_id)
    if not user or not resume:
        raise HTTPException(status_code=404, detail="User or resume not found")

    jobs = [JOBS[job_id] for job_id in payload.job_ids if job_id in JOBS]
    if not jobs:
        raise HTTPException(status_code=404, detail="No valid jobs found for provided job_ids")

    assessments = [assess_qualification(user, resume, job) for job in jobs]
    records, submitted, needs_user_input = run_auto_apply_from_assessments(
        user=user,
        resume=resume,
        jobs=jobs,
        assessments=assessments,
        min_ai_score=payload.min_ai_score,
        max_apply=payload.max_apply,
    )
    for record in records:
        APPLICATIONS[record.application_id] = record

    qualified_jobs = len([assessment for assessment in assessments if assessment.score >= payload.min_ai_score])
    return DiscoverAndAutoApplyResult(
        user_id=payload.user_id,
        provider="specific-selection",
        discovered_jobs=len(jobs),
        qualified_jobs=min(qualified_jobs, payload.max_apply),
        submitted=submitted,
        needs_user_input=needs_user_input,
        application_ids=[record.application_id for record in records],
        assessments=sorted(assessments, key=lambda item: item.score, reverse=True),
    )


@app.get("/automation/tasks/{task_id}")
def get_automation_task(task_id: str) -> dict:
    task = AUTOMATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/applications/browser-apply", response_model=ApplicationRecord)
def browser_apply(payload: BrowserApplyRequest) -> ApplicationRecord:
    user = USERS.get(payload.user_id)
    resume = RESUMES.get(payload.user_id)
    job = JOBS.get(payload.job_id)
    if not user or not resume or not job:
        raise HTTPException(status_code=404, detail="User, resume, or job not found")

    try:
        record = apply_with_browser_adapter(
            user=user,
            resume=resume,
            job=job,
            provider=payload.provider,
            storage_state_path=payload.storage_state_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    APPLICATIONS[record.application_id] = record
    return record

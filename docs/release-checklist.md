# Release Checklist

Use this before each public push or demo.

## Code Quality

- Run backend compile check:
  - `python -m py_compile app/*.py app/job_sources/*.py app/adapters/*.py`
- Run tests:
  - `PYTHONPATH=. python -m pytest -q`
- Confirm app boots locally:
  - `uvicorn app.main:app --reload`

## Documentation

- Update root `README.md` feature list if behavior changed.
- Update `backend/README.md` for any API/env changes.
- Add or refresh screenshots in `docs/images/`.

## Recruiter Positioning

- Confirm role keywords still present in README:
  - Business Analyst
  - Data Scientist
  - AI / Applied ML
- Keep `docs/resume-bullets.md` aligned with latest project scope.

## GitHub Hygiene

- Push to `main` with clear commit message.
- Add release tag for major milestones (`vX.Y.Z`).
- Confirm topics remain set in GitHub repo settings.
- Keep this repo pinned in profile.

## Demo Readiness

- Prepare one sample query and one domain-filtered query.
- Verify discovered jobs table shows selectable rows.
- Verify selected job bulk apply flow works.
- Verify at least one `needs_user_input` scenario can be shown.

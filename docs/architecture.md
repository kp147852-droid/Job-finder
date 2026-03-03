# Production Architecture (Recommended)

## 1) Core Services

- API Gateway: Auth, rate limits, request validation.
- User Service: Profiles, preferences, notification settings.
- Resume Service: Parsing, normalization, versioning.
- Matching Service: Ranking and fit scoring.
- Job Ingestion Service: Pull jobs from approved provider feeds/APIs.
- Application Orchestrator: Drives apply workflows and state machine.
- Alert Service: Sends "needs input" prompts to users.
- Admin/Audit Service: Logs actions for traceability.

## 2) Data & Infra

- Postgres: users, resumes, jobs, applications, audit logs.
- Redis: queues for application tasks and retries.
- Object storage: encrypted resume files and artifacts.
- Secrets manager: OAuth tokens and encrypted credentials.

## 3) Site Integration Strategy

- Prefer official APIs and partner programs when available.
- For employer sites, use a user-controlled browser automation/extension model.
- Never perform hidden submissions; require explicit user consent and visible activity logs.
- Respect robots/TOS and platform automation policies.

## 4) Human-in-the-loop Flow

1. Orchestrator starts application.
2. Adapter attempts form fill.
3. If unknown/required field appears, mark `needs_user_input`.
4. Alert user with exact field + reason.
5. User responds in app.
6. Orchestrator resumes from checkpoint and submits.

## 5) Multi-user & Security

- OAuth (Google/Microsoft/Email magic links).
- Tenant-safe row-level security.
- Encryption at rest + transit.
- Scoped provider tokens and periodic re-auth.
- Full audit trails for all application attempts.

## 6) Monetization-ready Features

- Free tier with monthly application cap.
- Pro tier with advanced filters, ATS scoring, and priority queues.
- Team/recruiter dashboards for B2B version.

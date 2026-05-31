# API Design

OpenAPI is available at `/docs` when the FastAPI service is running.

## Candidates

- `POST /api/candidates`: create onboarding profile.
- `GET /api/candidates/{candidate_id}`: fetch candidate profile.

## Jobs

- `POST /api/jobs/search`: aggregate and normalize jobs.
- `POST /api/jobs/sync`: manually sync configured ATS feeds into PostgreSQL.
- `GET /api/jobs/{job_id}`: fetch job detail.
- `POST /api/jobs/{job_id}/score`: score job against candidate context.

## Materials

- `POST /api/materials/generate`: generate truthful ATS resume draft, cover letter, recruiter message, LinkedIn message, follow-up email, and ATS score.

## Applications

- `POST /api/applications`: create manual, one-click, or smart auto-apply record.
- `GET /api/applications`: list pipeline records.

## Assistant

- `POST /api/assistant/chat`: career-data chat endpoint.

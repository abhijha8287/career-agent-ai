# JobHunter AI

JobHunter AI is a production-ready SaaS scaffold for AI-powered job, internship, and freelance opportunity discovery. It ingests public ATS job feeds, stores normalized jobs in PostgreSQL, exposes search APIs, ranks opportunities, generates application materials, and provides a Next.js dashboard for users.

## Current Features

- Next.js, React, TypeScript, and Tailwind frontend.
- FastAPI backend with OpenAPI docs.
- PostgreSQL-backed job storage.
- Real ATS ingestion for:
  - Greenhouse
  - Lever
  - Ashby
  - Workable
  - Recruitee
  - Personio
- Reddit jobs and freelance posts from `r/forhire`, `r/jobs`, `r/remotework`, and `r/remotejobs`.
- Playwright-based enterprise ATS crawlers for Workday, SuccessFactors, iCIMS, and Taleo.
- Personalized AI ranking with semantic, skill, experience, and location scores.
- Resume upload for PDF, DOCX, and TXT files.
- Job-click resume generation with JD extraction, keyword extraction, ATS optimization, three stored resume versions, and cover letter output.
- Deduplication by `source`, `external_job_id`, `company`, and `apply_url`.
- Celery worker plus Celery Beat scheduled sync every 30 minutes.
- Manual sync endpoint: `POST /api/jobs/sync`.
- Search endpoint backed by stored jobs: `POST /api/jobs/search`.
- AI matching and application material generation service boundaries.
- Docker Compose, Dockerfiles, Kubernetes manifests, and GitHub Actions CI.
- Architecture, API, schema, and deployment docs in `docs/`.

## Project Structure

```text
backend/              FastAPI API, SQLAlchemy models, ATS connectors, Celery tasks, tests
frontend/             Next.js application dashboard
infra/k8s/            Kubernetes manifests
docs/                 Architecture, API, database schema, deployment guide
docker-compose.yml    Local full-stack services
.github/workflows/    CI pipeline
```

## Configure ATS Ingestion

Copy the backend example env file and edit the board/account lists:

```powershell
Copy-Item backend\.env.example backend\.env
```

Example values:

```env
GREENHOUSE_BOARDS=["openai","stripe"]
LEVER_SITES=["lever"]
ASHBY_BOARDS=["ashby"]
WORKABLE_ACCOUNTS=["account-slug"]
RECRUITEE_COMPANIES=["company-subdomain"]
PERSONIO_COMPANIES=["company-subdomain"]
REDDIT_SUBREDDITS=["forhire","jobs","remotework","remotejobs"]
REDDIT_USER_AGENT=JobHunterAI/0.1 contact:local-dev
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
WORKDAY_CAREER_URLS=["https://company.wd1.myworkdayjobs.com/careers"]
SUCCESSFACTORS_CAREER_URLS=[]
ICIMS_CAREER_URLS=[]
TALEO_CAREER_URLS=[]
```

These are public employer-specific feeds. For example, `GREENHOUSE_BOARDS=["openai"]` reads OpenAI's public Greenhouse board token. Empty lists are allowed.

For Reddit, create an app at https://www.reddit.com/prefs/apps and set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. The connector tries official OAuth first, then RSS, then anonymous JSON. OAuth is the most reliable option because Reddit often blocks anonymous JSON with HTTP 403.

For enterprise ATS crawling, install Playwright browser binaries after installing backend requirements:

```powershell
cd backend
.\.venv\Scripts\python.exe -m playwright install chromium
```

The Workday, SuccessFactors, iCIMS, and Taleo connectors open configured career URLs with Playwright, intercept network JSON responses, extract jobs from API payloads, and normalize them into the same PostgreSQL job table.

## Run With Docker Compose

From the repository root:

```powershell
docker compose up --build
```

Default URLs:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Docker Compose starts:

- `postgres`
- `redis`
- `elasticsearch`
- `backend`
- `worker`
- `beat`
- `frontend`

The `beat` service runs the ATS sync task every 30 minutes.

## Run Manually

If ports `3000` or `8000` are already in use, choose different ports. During development in this workspace, the app has been run on frontend port `3010` and backend port `8010`.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010
```

Backend URLs:

- API docs: http://127.0.0.1:8010/docs
- Health: http://127.0.0.1:8010/health

### Frontend

```powershell
cd frontend
npm.cmd install
$env:NEXT_PUBLIC_API_URL="http://localhost:8010"
npm.cmd run dev -- --port 3010
```

Frontend URL:

- http://127.0.0.1:3010

If you see `500 Internal Server Error` on port `3010`, stop the old dev server, clear the Next cache, and restart:

```powershell
netstat -ano | Select-String ':3010'
Stop-Process -Id <PID_FROM_LISTENING_ROW> -Force
cd frontend
npm.cmd run clean
npm.cmd run dev:3010
```

Keep that terminal open while using the app.

### Celery Worker And Beat

Run these in separate terminals after Redis is available:

```powershell
cd backend
.\.venv\Scripts\python.exe -m celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m celery -A app.tasks.celery_app.celery_app beat --loglevel=INFO
```

On Windows, the app config uses Celery's `solo` worker pool to avoid `PermissionError: [WinError 5] Access is denied` from the default prefork pool. If you still pass flags manually, use:

```powershell
.\.venv\Scripts\python.exe -m celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO --pool=solo --concurrency=1
```

## Sync And Search Jobs

Trigger a manual sync:

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8010/api/jobs/sync
```

Search stored jobs:

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query":"engineer","location":"remote","limit":10}' `
  http://127.0.0.1:8010/api/jobs/search
```

Filter by source:

```json
{
  "query": "engineer",
  "location": "remote",
  "source": "greenhouse",
  "limit": 10
}
```

Supported source values include `greenhouse`, `lever`, `ashby`, `workable`, `recruitee`, `personio`, and `reddit`.
Enterprise source values include `workday`, `successfactors`, `icims`, and `taleo`.

To personalize ranking, pass `candidate_profile` to `/api/jobs/search`:

```json
{
  "query": "python engineer",
  "source": "workday",
  "limit": 10,
  "candidate_profile": {
    "skills": ["Python", "React", "AWS"],
    "preferred_locations": ["Remote", "Bengaluru"],
    "years_experience": 3,
    "resume_text": "Python backend engineer with React and AWS experience"
  }
}
```

Final score uses:

- 40% semantic match from resume/job embeddings
- 30% skill match
- 20% experience match
- 10% location match

## Resume Upload Ranking

The frontend includes a `Resume Ranking` panel. Upload a `.pdf`, `.docx`, or `.txt` resume and the backend will:

- Extract resume text.
- Detect common technical skills.
- Build a candidate profile.
- Send the resume text and profile into job search.
- Rank jobs with the weighted AI ranking model.

Backend endpoint:

```text
POST /api/candidates/resume
```

The search response includes:

- `match_score`
- `semantic_match_score`
- `skill_match_score`
- `experience_fit_score`
- `location_fit_score`

## Resume Generation

After uploading a resume, click the document icon on any job card. The app will:

- Extract the selected job description.
- Extract ATS keywords from required skills, preferred skills, title, and description.
- Compare those keywords against the uploaded resume profile.
- Generate `resume_v1`, `resume_v2`, and `resume_v3`.
- Generate a tailored cover letter, recruiter message, LinkedIn message, and follow-up email.
- Preview generated resume and cover letter in a formatted document view.
- Download the tailored resume or cover letter as a styled PDF.
- Store each generated resume version in PostgreSQL when the database is available.

Backend endpoint:

```text
POST /api/materials/generate
POST /api/materials/pdf
```

Request body shape:

```json
{
  "candidate_id": "uploaded-candidate-id",
  "job_id": "stored-job-id",
  "candidate_profile": {},
  "job": {}
}
```

For live fallback jobs that are not stored yet, the frontend sends the selected job payload directly. For stored jobs, the backend can load the job by `job_id`.

## Validation

Backend:

```powershell
python -m compileall backend\app backend\tests
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
```

## Deployment

Kubernetes manifests are in `infra/k8s/`:

- `backend.yaml`
- `frontend.yaml`
- `worker.yaml`
- `ingress.yaml`

Production should provide these secrets/config values:

- `DATABASE_URL`
- `REDIS_URL`
- `ELASTICSEARCH_URL`
- `OPENAI_API_KEY`
- `S3_BUCKET`
- `AWS_REGION`
- `AUTH_ISSUER`
- `GREENHOUSE_BOARDS`
- `LEVER_SITES`
- `ASHBY_BOARDS`
- `WORKABLE_ACCOUNTS`
- `RECRUITEE_COMPANIES`
- `PERSONIO_COMPANIES`

See `docs/deployment-guide.md` for the AWS deployment shape.

## Compliance

JobHunter AI is designed to respect platform terms. Connectors use official APIs, public job-board APIs, public XML feeds, or employer-published career feeds where available. Restricted application submission workflows should remain browser-assisted and require explicit user approval before final submission.

# JobHunter AI (career-agent-ai)

A job-discovery app that collects openings from public ATS feeds and job boards, ranks them against your resume, and drafts tailored resumes and cover letters.

## Why this exists
Job searching means checking dozens of company career pages by hand. This pulls them into one database, scores each role against a profile, and prepares application material for the ones worth applying to.

## What it does
- Ingests jobs from Greenhouse, Lever, Ashby, Workable, Recruitee and Personio feeds
- Crawls Workday, SuccessFactors, iCIMS and Taleo career sites with Playwright
- Collects job and freelance posts from selected subreddits
- De-duplicates by source, job ID, company and apply URL; syncs every 30 minutes with Celery Beat
- Parses uploaded resumes (PDF, DOCX, TXT) and ranks jobs by semantic, skill, experience and location fit
- For a chosen job: extracts the description's keywords and generates three resume versions and a cover letter

## Project structure
```
career-agent-ai/
├── backend/
│   ├── app/api/       FastAPI routes
│   ├── app/services/  Ingestion, ranking, resume generation
│   ├── app/tasks/     Celery sync jobs
│   ├── app/models/    Database tables
│   ├── app/schemas/   Request and response models
│   ├── app/db/        Database session setup
│   ├── app/core/      Settings
│   └── tests/         pytest suite
├── frontend/          Next.js app
├── infra/k8s/         Kubernetes manifests
├── docs/              Architecture, API, schema, deployment
├── .github/workflows/ CI pipeline
└── docker-compose.yml Full local stack
```

## Getting started
Requirements: Docker and Docker Compose (or Python 3.11+, Node.js 18+, PostgreSQL and Redis to run manually).
```bash
git clone https://github.com/abhijha8287/career-agent-ai.git
cd career-agent-ai
cp backend/.env.example backend/.env
docker compose up --build
```
| Service | Address |
|:--|:--|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

Compose starts Postgres, Redis, Elasticsearch, the backend, a Celery worker, Celery Beat and the frontend.

Run without Docker:
```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
cd ../frontend && npm install && npm run dev
```

## Configuration
| Variable | Purpose |
|:--|:--|
| `DATABASE_URL`, `REDIS_URL`, `ELASTICSEARCH_URL` | Data stores |
| `CORS_ORIGINS` | Allowed frontend URLs |
| `GREENHOUSE_BOARDS`, `LEVER_SITES`, `ASHBY_BOARDS`, `WORKABLE_ACCOUNTS`, `RECRUITEE_COMPANIES`, `PERSONIO_COMPANIES` | Which company feeds to pull |
| `WORKDAY_CAREER_URLS`, `SUCCESSFACTORS_CAREER_URLS`, `ICIMS_CAREER_URLS`, `TALEO_CAREER_URLS` | Career sites to crawl |
| `REDDIT_SUBREDDITS`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` | Reddit source |
| `OPENAI_EMBEDDING_MODEL` | Embedding model for ranking |
| `APP_ENV` | Environment name |

## Tests
```bash
cd backend && pytest
cd frontend && npm run typecheck && npm run build
```

## Tech stack
Python, FastAPI, PostgreSQL, Redis, Celery, Elasticsearch, Playwright, pypdf, python-docx, OpenAI embeddings, Next.js, React, TypeScript, Tailwind CSS, Docker, Kubernetes, GitHub Actions

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

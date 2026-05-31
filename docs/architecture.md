# Architecture

JobHunter AI is organized as a microservice-ready monorepo.

## Services

- `frontend`: Next.js web app for onboarding, opportunity search, job detail pages, application tracker, analytics, and assistant.
- `backend`: FastAPI API service exposing candidate, job, material, application, and assistant endpoints.
- `worker`: Celery worker for scheduled monitoring, enrichment, material generation, notifications, and browser-assisted application preparation.
- `postgres`: System of record for candidates, jobs, applications, generated materials, connector runs, and audit logs.
- `redis`: Broker/cache for background jobs and rate-limit state.
- `elasticsearch`: Search index for jobs, resumes, skill trends, and semantic retrieval metadata.
- `s3`: File storage for resumes, DOCX/PDF exports, cover letters, and source attachments.

## Connector Model

Each connector implements `JobConnector.search(query, location, limit)` and `fetch_all()` and returns normalized `ConnectorJob` records. Official APIs and public feeds should be preferred. Restricted platforms should use browser-assisted workflows and must require explicit approval before final application submission.

Supported connector families:

- Job boards: LinkedIn, Indeed, Glassdoor, Wellfound, Naukri, Foundit, Internshala, CutShort, RemoteOK, WeWorkRemotely, FlexJobs.
- Freelance: Upwork, Freelancer, Toptal, PeoplePerHour, Guru, Fiverr.
- ATS: Greenhouse, Lever, Ashby, Workday, SmartRecruiters, BambooHR, public company career pages.
- Communities: Reddit job communities and curated public feeds.

## Real ATS Ingestion

The implemented ingestion service supports real public-per-employer feeds for:

- Greenhouse: `GREENHOUSE_BOARDS=["openai","stripe"]`
- Lever: `LEVER_SITES=["netflix","lever"]`
- Ashby: `ASHBY_BOARDS=["ashby"]`
- Workable: `WORKABLE_ACCOUNTS=["account-slug"]`
- Recruitee: `RECRUITEE_COMPANIES=["company-subdomain"]`
- Personio: `PERSONIO_COMPANIES=["company-subdomain"]`
- Reddit: `REDDIT_SUBREDDITS=["forhire","jobs","remotework","remotejobs"]`

Reddit supports `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` for official OAuth access. The fallback order is OAuth, RSS, then anonymous JSON.

Enterprise ATS connectors support Playwright network interception for:

- Workday: `WORKDAY_CAREER_URLS`
- SuccessFactors: `SUCCESSFACTORS_CAREER_URLS`
- iCIMS: `ICIMS_CAREER_URLS`
- Taleo: `TALEO_CAREER_URLS`

The crawler opens each configured career URL, captures JSON network responses, recursively extracts job-like objects, normalizes title, description, location, apply URL, external job ID, and inferred skills, then stores through the same dedupe path.

## AI Ranking

Personalized ranking uses:

- Resume embedding and job embedding semantic similarity.
- Skill match score from required and preferred skills.
- Experience fit from years-of-experience requirements parsed from the job.
- Location fit from user preferred locations and remote matching.

Final score:

`40% semantic match + 30% skills + 20% experience + 10% location`

OpenAI embeddings are used when `OPENAI_API_KEY` is configured. Local deterministic hashing embeddings are used as a development fallback.

Celery Beat runs `app.tasks.jobs.sync_ats_jobs` every 30 minutes. The API also exposes `POST /api/jobs/sync` for manual syncs. Jobs and Reddit freelance posts are upserted into PostgreSQL using `(source, external_job_id, company, apply_url)`.

## AI Workflows

- Candidate profile extraction from resume and linked profiles.
- Job description cleaning and skill extraction.
- Match score from skills, compensation, location, experience, and user preferences.
- Resume optimization with a strict no-fabrication policy.
- Cover letter, recruiter message, LinkedIn message, follow-up email, and freelance proposal generation.
- Career agent recommendations using embeddings and retrieved career context.

## Compliance

The application stores an approval log for automated flows. Smart auto-apply can prepare application packets, but final submission is gated when platform rules require browser interaction or user consent.

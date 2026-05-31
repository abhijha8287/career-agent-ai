# Deployment Guide

## Local

```powershell
docker compose up --build
```

## Production AWS Shape

- EKS for frontend, backend, worker deployments.
- RDS PostgreSQL for durable data.
- ElastiCache Redis for queue and cache.
- OpenSearch or Elastic Cloud for opportunity and skill search.
- S3 for generated documents and uploads.
- CloudFront and WAF for frontend delivery and protection.
- Secrets Manager for API keys, database credentials, Clerk/Auth0 secrets, and OpenAI keys.
- Prometheus and Grafana for metrics.

## Required Secrets

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
- `REDDIT_SUBREDDITS`
- `REDDIT_USER_AGENT`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `WORKDAY_CAREER_URLS`
- `SUCCESSFACTORS_CAREER_URLS`
- `ICIMS_CAREER_URLS`
- `TALEO_CAREER_URLS`
- `OPENAI_EMBEDDING_MODEL`

## Release Steps

1. Build and push backend and frontend images.
2. Apply Kubernetes secrets.
3. Apply `infra/k8s/*.yaml`.
4. Run database migrations.
5. Verify `/health`, `/docs`, frontend login, and one connector run.
6. Run the worker and beat deployments. Beat syncs ATS jobs every 30 minutes.

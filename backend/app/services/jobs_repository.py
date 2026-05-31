from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.domain import Job
from app.services.connectors.base import ConnectorJob
from app.services.job_search import clean_description


def _job_values(job: ConnectorJob) -> dict:
    now = datetime.now(UTC)
    return {
        "source": job.source,
        "external_job_id": job.external_job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "employment_type": job.employment_type or "full_time",
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "responsibilities": job.responsibilities,
        "benefits": job.benefits,
        "deadline": job.deadline,
        "apply_url": job.apply_url,
        "original_description": job.original_description,
        "cleaned_description": clean_description(job.original_description),
        "company_details": job.company_details,
        "raw_payload": {
            **job.raw_payload,
            "budget": job.budget,
            "author": job.author,
            "posted_date": job.posted_date,
        },
        "last_seen_at": now,
        "updated_at": now,
    }


class JobsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, jobs: list[ConnectorJob]) -> int:
        if not jobs:
            return 0

        rows = [_job_values(job) for job in jobs if job.external_job_id and job.company and job.apply_url]
        if not rows:
            return 0

        stmt = insert(Job).values(rows)
        update_columns = {
            column.name: getattr(stmt.excluded, column.name)
            for column in Job.__table__.columns
            if column.name not in {"id", "created_at"}
        }
        stmt = stmt.on_conflict_do_update(
            constraint="uq_jobs_source_external_company_apply_url",
            set_=update_columns,
        )
        self.db.execute(stmt)
        self.db.commit()
        return len(rows)

    def search(self, query: str | None, location: str | None, source: str | None, limit: int) -> list[Job]:
        stmt = select(Job).order_by(Job.last_seen_at.desc()).limit(limit)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Job.title.ilike(pattern), Job.company.ilike(pattern), Job.cleaned_description.ilike(pattern)))
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))
        if source:
            stmt = stmt.where(Job.source == source)
        return list(self.db.scalars(stmt).all())

    def get(self, job_id: str) -> Job | None:
        return self.db.get(Job, UUID(job_id))

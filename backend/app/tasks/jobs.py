from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.job_ingestion import JobIngestionService


@celery_app.task(name="app.tasks.jobs.monitor_candidate_jobs")
def monitor_candidate_jobs(candidate_id: str) -> dict:
    return {"candidate_id": candidate_id, "status": "queued"}


@celery_app.task(name="app.tasks.jobs.sync_ats_jobs")
def sync_ats_jobs() -> list[dict]:
    db = SessionLocal()
    try:
        return JobIngestionService(db).sync_all_sync()
    finally:
        db.close()

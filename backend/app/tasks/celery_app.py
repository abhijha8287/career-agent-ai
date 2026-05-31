import platform

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "jobhunter_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.jobs"],
)
celery_app.conf.task_default_queue = "jobs"
celery_app.conf.task_routes = {"app.tasks.jobs.*": {"queue": "jobs"}}
if platform.system() == "Windows":
    celery_app.conf.worker_pool = "solo"
    celery_app.conf.worker_concurrency = 1
celery_app.conf.beat_schedule = {
    "sync-ats-jobs-every-30-minutes": {
        "task": "app.tasks.jobs.sync_ats_jobs",
        "schedule": 30 * 60,
    }
}

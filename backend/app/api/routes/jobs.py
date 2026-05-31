from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.api import JobOut, JobSearchRequest, MatchScoreOut
from app.services.ai.matching import MatchingService
from app.services.job_search import JobSearchService, clean_description
from app.services.job_ingestion import JobIngestionService
from app.services.jobs_repository import JobsRepository
from app.db.session import get_db

router = APIRouter()


def _with_score(payload: dict, score: dict | None) -> dict:
    if not score:
        return payload
    payload.update(
        {
            "match_score": score["match_score"],
            "semantic_match_score": score["semantic_match_score"],
            "skill_match_score": score["skill_match_score"],
            "experience_fit_score": score["experience_fit_score"],
            "location_fit_score": score["location_fit_score"],
        }
    )
    return payload


def _to_job_out(job: object, score: dict | None = None) -> JobOut:
    payload = dict(
        id=str(job.id),
        source=job.source,
        external_job_id=job.external_job_id,
        title=job.title,
        company=job.company,
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        employment_type=job.employment_type,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        apply_url=job.apply_url,
        cleaned_description=job.cleaned_description,
        company_details=job.company_details,
        last_seen_at=job.last_seen_at.isoformat() if job.last_seen_at else None,
        budget=(job.raw_payload or {}).get("budget") or (job.company_details or {}).get("budget"),
        author=(job.raw_payload or {}).get("author") or (job.company_details or {}).get("author"),
        posted_date=(job.raw_payload or {}).get("posted_date") or (job.company_details or {}).get("posted_date"),
        link=(job.company_details or {}).get("link") or job.apply_url,
    )
    return JobOut(**_with_score(payload, score))


def _connector_job_to_out(job: object, score: dict | None = None) -> JobOut:
    payload = dict(
        id=f"{job.source}:{job.external_job_id}",
        source=job.source,
        external_job_id=job.external_job_id,
        title=job.title,
        company=job.company,
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        employment_type=job.employment_type,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        apply_url=job.apply_url,
        cleaned_description=clean_description(job.original_description),
        company_details={**job.company_details, "storage": "live_fallback"},
        last_seen_at=None,
        budget=job.budget,
        author=job.author,
        posted_date=job.posted_date,
        link=job.apply_url,
    )
    return JobOut(**_with_score(payload, score))


def _score_stored_job(candidate: dict | None, job: object) -> dict | None:
    if not candidate:
        return None
    job_payload = {
        "title": job.title,
        "company": job.company,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "responsibilities": job.responsibilities,
        "cleaned_description": job.cleaned_description,
        "location": job.location,
        "salary_max": job.salary_max,
    }
    return MatchingService().score(candidate, job_payload)


@router.post("/search", response_model=list[JobOut])
async def search_jobs(payload: JobSearchRequest, db: Session = Depends(get_db)) -> list[JobOut]:
    try:
        jobs = JobsRepository(db).search(payload.query, payload.location, payload.source, payload.limit)
        if jobs:
            scored = [(job, _score_stored_job(payload.candidate_profile, job)) for job in jobs]
            if payload.candidate_profile:
                scored.sort(key=lambda item: item[1]["match_score"] if item[1] else 0, reverse=True)
            return [_to_job_out(job, score) for job, score in scored]
    except SQLAlchemyError:
        pass

    try:
        live_jobs = await JobSearchService().search(payload.query, payload.location, payload.limit, payload.source)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{payload.source or 'Live'} connector failed: {exc}") from exc
    scored_live = [(job, MatchingService().score(payload.candidate_profile, job) if payload.candidate_profile else None) for job in live_jobs]
    if payload.candidate_profile:
        scored_live.sort(key=lambda item: item[1]["match_score"] if item[1] else 0, reverse=True)
    return [_connector_job_to_out(job, score) for job, score in scored_live]


@router.post("/sync")
async def sync_jobs(db: Session = Depends(get_db)) -> list[dict]:
    results = await JobIngestionService(db).sync_all()
    return [result.__dict__ for result in results]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    job = JobsRepository(db).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_job_out(job)


@router.post("/{job_id}/score", response_model=MatchScoreOut)
def score_job(job_id: str, candidate: dict, db: Session = Depends(get_db)) -> MatchScoreOut:
    job = JobsRepository(db).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job_payload = {
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "responsibilities": job.responsibilities,
        "title": job.title,
        "company": job.company,
        "cleaned_description": job.cleaned_description,
        "location": job.location,
        "salary_max": job.salary_max,
    }
    return MatchScoreOut(**MatchingService().score(candidate, job_payload))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.candidates import _candidates
from app.db.session import get_db
from app.models.domain import GeneratedMaterial
from app.schemas.api import GeneratedMaterialOut, MaterialRequest
from app.services.ai.materials import MaterialGenerationService
from app.services.jobs_repository import JobsRepository

router = APIRouter()


@router.post("/generate", response_model=GeneratedMaterialOut)
def generate_materials(payload: MaterialRequest, db: Session = Depends(get_db)) -> GeneratedMaterialOut:
    candidate = payload.candidate_profile
    if not candidate and payload.candidate_id:
        candidate = _candidates.get(payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=400, detail="Upload a resume before generating materials")

    job_payload = payload.job
    if not job_payload and payload.job_id:
        try:
            job = JobsRepository(db).get(payload.job_id)
        except (ValueError, SQLAlchemyError):
            job = None
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        job_payload = {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "responsibilities": job.responsibilities,
            "cleaned_description": job.cleaned_description,
            "original_description": job.original_description,
        }
    if not job_payload:
        raise HTTPException(status_code=400, detail="Select a job before generating materials")

    materials = MaterialGenerationService().generate(candidate, job_payload)
    _store_versions(db, payload, job_payload, materials)
    return GeneratedMaterialOut(**materials)


def _store_versions(db: Session, payload: MaterialRequest, job: dict, materials: dict) -> None:
    candidate_id = payload.candidate_id or str((payload.candidate_profile or {}).get("id") or "uploaded-resume")
    job_id = payload.job_id or str(job.get("id") or job.get("external_job_id") or job.get("apply_url") or "selected-job")
    rows = [
        GeneratedMaterial(
            candidate_id=candidate_id,
            job_id=job_id,
            version_label=version["label"],
            focus=version["focus"],
            resume_markdown=version["resume_markdown"],
            cover_letter=materials["cover_letter"],
            keywords=materials["keywords"],
            matched_keywords=materials["matched_keywords"],
            missing_keywords=materials["missing_keywords"],
            ats_score=materials["ats_score"],
        )
        for version in materials["versions"]
    ]
    try:
        db.add_all(rows)
        db.commit()
    except SQLAlchemyError:
        db.rollback()

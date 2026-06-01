from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.schemas.api import CandidateCreate, CandidateOut
from app.services.resume_parser import extract_candidate_name, extract_skills, parse_resume, summarize_resume

router = APIRouter()

_candidates: dict[str, dict] = {}


@router.post("", response_model=CandidateOut)
def create_candidate(payload: CandidateCreate) -> CandidateOut:
    candidate = payload.model_dump(mode="json")
    candidate["id"] = str(uuid4())
    candidate["profile_summary"] = (
        f"{payload.full_name} is targeting {', '.join(payload.preferred_roles) or 'new opportunities'} "
        f"with skills in {', '.join(payload.skills[:8])}."
    )
    _candidates[candidate["id"]] = candidate
    return CandidateOut(**candidate)


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str) -> CandidateOut:
    return CandidateOut(**_candidates[candidate_id])


@router.post("/resume", response_model=CandidateOut)
async def upload_resume(
    resume: UploadFile = File(...),
    full_name: str | None = None,
    email: str = "resume-user@example.com",
) -> CandidateOut:
    content = await resume.read()
    resume_text = parse_resume(resume.filename or "resume.txt", content)
    skills = extract_skills(resume_text)
    candidate_name = full_name or extract_candidate_name(resume_text)
    candidate = {
        "id": str(uuid4()),
        "email": email,
        "full_name": candidate_name,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "skills": skills,
        "preferred_roles": [],
        "preferred_locations": [],
        "salary_expectation": None,
        "work_mode": "remote",
        "opportunity_type": "full_time",
        "visa_sponsorship_required": False,
        "years_experience": 0,
        "profile_summary": summarize_resume(resume_text),
        "resume_text": resume_text,
        "resume_filename": resume.filename,
    }
    _candidates[candidate["id"]] = candidate
    return CandidateOut(**candidate)

from uuid import uuid4

from fastapi import APIRouter

from app.schemas.api import ApplicationCreate

router = APIRouter()
_applications: dict[str, dict] = {}


@router.post("")
def create_application(payload: ApplicationCreate) -> dict:
    app_id = str(uuid4())
    application = {
        "id": app_id,
        "candidate_id": payload.candidate_id,
        "job_id": payload.job_id,
        "mode": payload.mode,
        "stage": "saved" if payload.require_approval else "applied",
        "log": [
            {
                "event": "application_created",
                "message": "Application package prepared. User approval is required before submission.",
            }
        ],
    }
    _applications[app_id] = application
    return application


@router.get("")
def list_applications() -> list[dict]:
    return list(_applications.values())

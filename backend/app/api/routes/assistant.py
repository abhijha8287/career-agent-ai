from fastapi import APIRouter

from app.schemas.api import AssistantRequest

router = APIRouter()


@router.post("/chat")
def chat(payload: AssistantRequest) -> dict[str, str]:
    return {
        "answer": (
            "I can search matching roles, explain ranking, identify skill gaps, improve application materials, "
            "and recommend portfolio or certification work based on your career profile."
        )
    }

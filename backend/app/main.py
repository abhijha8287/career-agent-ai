from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import applications, assistant, candidates, jobs, materials
from app.core.config import settings
from app.db.session import Base, engine


app = FastAPI(
    title="JobHunter AI API",
    version="0.1.0",
    description="AI-powered job, internship, and freelance opportunity platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])


@app.on_event("startup")
def create_tables() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        print(f"Database unavailable during startup; continuing without table creation: {exc}")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jobhunter-ai"}

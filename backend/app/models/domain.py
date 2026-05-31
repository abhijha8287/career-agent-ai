import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WorkMode(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"


class OpportunityType(str, enum.Enum):
    full_time = "full_time"
    internship = "internship"
    freelance = "freelance"


class ApplicationStage(str, enum.Enum):
    saved = "saved"
    applied = "applied"
    assessment = "assessment"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    salary_expectation: Mapped[int | None] = mapped_column(Integer)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode), default=WorkMode.remote)
    opportunity_type: Mapped[OpportunityType] = mapped_column(Enum(OpportunityType), default=OpportunityType.full_time)
    visa_sponsorship_required: Mapped[bool] = mapped_column(default=False)
    years_experience: Mapped[float] = mapped_column(Float, default=0)
    profile_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="candidate")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_job_id",
            "company",
            "apply_url",
            name="uq_jobs_source_external_company_apply_url",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80), index=True)
    external_job_id: Mapped[str] = mapped_column(String(250), index=True)
    title: Mapped[str] = mapped_column(String(250), index=True)
    company: Mapped[str] = mapped_column(String(250), index=True)
    location: Mapped[str | None] = mapped_column(String(250))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    employment_type: Mapped[str] = mapped_column(String(80), default=OpportunityType.full_time.value)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    deadline: Mapped[str | None] = mapped_column(String(80))
    apply_url: Mapped[str] = mapped_column(String(1000))
    original_description: Mapped[str] = mapped_column(Text)
    cleaned_description: Mapped[str] = mapped_column(Text)
    company_details: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"))
    stage: Mapped[ApplicationStage] = mapped_column(Enum(ApplicationStage), default=ApplicationStage.saved)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    resume_version_url: Mapped[str | None] = mapped_column(String(1000))
    cover_letter_url: Mapped[str | None] = mapped_column(String(1000))
    log: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")


class GeneratedMaterial(Base):
    __tablename__ = "generated_materials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(String(80), index=True)
    job_id: Mapped[str] = mapped_column(String(120), index=True)
    version_label: Mapped[str] = mapped_column(String(40), index=True)
    focus: Mapped[str] = mapped_column(String(120))
    resume_markdown: Mapped[str] = mapped_column(Text)
    cover_letter: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    matched_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    ats_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

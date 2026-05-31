from pydantic import BaseModel, EmailStr, Field, HttpUrl


class CandidateCreate(BaseModel):
    email: EmailStr
    full_name: str
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    skills: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    salary_expectation: int | None = None
    work_mode: str = "remote"
    opportunity_type: str = "full_time"
    visa_sponsorship_required: bool = False
    years_experience: float = 0


class CandidateOut(CandidateCreate):
    id: str
    profile_summary: str | None = None
    resume_text: str | None = None
    resume_filename: str | None = None


class JobSearchRequest(BaseModel):
    query: str
    location: str | None = None
    source: str | None = None
    opportunity_type: str = "full_time"
    limit: int = 25
    candidate_profile: dict | None = None


class JobOut(BaseModel):
    id: str
    source: str
    external_job_id: str | None = None
    title: str
    company: str
    location: str | None
    salary_min: int | None
    salary_max: int | None
    employment_type: str
    required_skills: list[str]
    preferred_skills: list[str]
    apply_url: str
    cleaned_description: str
    company_details: dict
    last_seen_at: str | None = None
    budget: str | None = None
    author: str | None = None
    posted_date: str | None = None
    link: str | None = None
    match_score: int | None = None
    semantic_match_score: int | None = None
    skill_match_score: int | None = None
    experience_fit_score: int | None = None
    location_fit_score: int | None = None


class MatchScoreOut(BaseModel):
    match_score: int
    semantic_match_score: int
    skill_match_score: int
    skill_gap: list[str]
    location_fit_score: int
    experience_fit_score: int
    rationale: str


class MaterialRequest(BaseModel):
    candidate_id: str | None = None
    job_id: str | None = None
    candidate_profile: dict | None = None
    job: dict | None = None


class ResumeVersionOut(BaseModel):
    label: str
    focus: str
    resume_markdown: str


class GeneratedMaterialOut(BaseModel):
    resume_markdown: str
    cover_letter: str
    recruiter_message: str
    linkedin_message: str
    follow_up_email: str
    ats_score: int
    keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    versions: list[ResumeVersionOut]


class MaterialPdfRequest(BaseModel):
    document_title: str
    document_subtitle: str = ""
    document_body: str
    filename: str = "application-material.pdf"


class ApplicationCreate(BaseModel):
    candidate_id: str
    job_id: str
    mode: str = "manual"
    require_approval: bool = True


class AssistantRequest(BaseModel):
    candidate_id: str
    message: str

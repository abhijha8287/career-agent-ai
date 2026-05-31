from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://jobhunter:jobhunter@localhost:5432/jobhunter"
    redis_url: str = "redis://localhost:6379/0"
    elasticsearch_url: str = "http://localhost:9200"
    openai_api_key: str | None = None
    s3_bucket: str | None = None
    aws_region: str = "us-east-1"
    auth_issuer: str | None = None
    cors_origins: list[AnyHttpUrl | str] = Field(default_factory=lambda: ["http://localhost:3000"])
    greenhouse_boards: list[str] = Field(default_factory=list)
    lever_sites: list[str] = Field(default_factory=list)
    ashby_boards: list[str] = Field(default_factory=list)
    workable_accounts: list[str] = Field(default_factory=list)
    recruitee_companies: list[str] = Field(default_factory=list)
    personio_companies: list[str] = Field(default_factory=list)
    reddit_subreddits: list[str] = Field(default_factory=lambda: ["forhire", "jobs", "remotework", "remotejobs"])
    reddit_user_agent: str = "JobHunterAI/0.1 contact:local-dev"
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    workday_career_urls: list[str] = Field(default_factory=list)
    successfactors_career_urls: list[str] = Field(default_factory=list)
    icims_career_urls: list[str] = Field(default_factory=list)
    taleo_career_urls: list[str] = Field(default_factory=list)
    openai_embedding_model: str = "text-embedding-3-small"


settings = Settings()

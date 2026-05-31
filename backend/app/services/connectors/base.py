from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ConnectorJob:
    source: str
    external_job_id: str
    title: str
    company: str
    location: str | None
    apply_url: str
    original_description: str
    employment_type: str = "full_time"
    salary_min: int | None = None
    salary_max: int | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    deadline: str | None = None
    company_details: dict = field(default_factory=dict)
    raw_payload: dict = field(default_factory=dict)
    budget: str | None = None
    author: str | None = None
    posted_date: str | None = None


class JobConnector(ABC):
    name: str
    supports_auto_apply: bool = False
    requires_browser_assist: bool = False

    @abstractmethod
    async def search(self, query: str, location: str | None, limit: int) -> list[ConnectorJob]:
        raise NotImplementedError

    async def fetch_all(self) -> list[ConnectorJob]:
        return await self.search(query="", location=None, limit=500)

import asyncio
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.connectors.registry import registry
from app.services.jobs_repository import JobsRepository


@dataclass
class SyncResult:
    source: str
    fetched: int
    stored: int
    error: str | None = None


class JobIngestionService:
    def __init__(self, db: Session) -> None:
        self.repository = JobsRepository(db)

    async def sync_all(self) -> list[SyncResult]:
        results: list[SyncResult] = []
        for connector in registry.all():
            if not self._is_configured(connector):
                continue
            try:
                jobs = await connector.fetch_all()
                stored = self.repository.upsert_many(jobs)
                results.append(SyncResult(source=connector.name, fetched=len(jobs), stored=stored))
            except Exception as exc:
                results.append(SyncResult(source=connector.name, fetched=0, stored=0, error=str(exc)))
        return results

    def sync_all_sync(self) -> list[dict]:
        return [result.__dict__ for result in asyncio.run(self.sync_all())]

    def _is_configured(self, connector: object) -> bool:
        for attr in ("boards", "subreddits", "career_urls"):
            if hasattr(connector, attr):
                return bool(getattr(connector, attr))
        return True

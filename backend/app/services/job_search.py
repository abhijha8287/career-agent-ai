import re

from app.services.connectors.base import ConnectorJob
from app.services.connectors.registry import registry


def clean_description(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class JobSearchService:
    async def search(
        self,
        query: str,
        location: str | None,
        limit: int,
        source: str | None = None,
    ) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        connectors = [
            connector
            for connector in registry.all()
            if self._is_configured(connector)
        ]
        if source:
            connectors = [connector for connector in connectors if connector.name == source]
        per_connector_limit = max(1, limit // max(1, len(connectors)))
        for connector in connectors:
            try:
                found = await connector.search(query=query, location=location, limit=per_connector_limit)
            except Exception:
                if source:
                    raise
                continue
            for job in found:
                job.original_description = job.original_description.strip()
            jobs.extend(found)
        return jobs[:limit]

    def _is_configured(self, connector: object) -> bool:
        for attr in ("boards", "subreddits", "career_urls"):
            if hasattr(connector, attr):
                return bool(getattr(connector, attr))
        return True

from app.services.connectors.base import JobConnector
from app.services.connectors.ats_sources import (
    AshbyConnector,
    GreenhouseConnector,
    LeverConnector,
    PersonioConnector,
    RecruiteeConnector,
    WorkableConnector,
)
from app.services.connectors.enterprise_crawler import (
    ICimsCrawlerConnector,
    SuccessFactorsCrawlerConnector,
    TaleoCrawlerConnector,
    WorkdayCrawlerConnector,
)
from app.services.connectors.reddit_sources import RedditJobsConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, JobConnector] = {}

    def register(self, connector: JobConnector) -> None:
        self._connectors[connector.name] = connector

    def all(self) -> list[JobConnector]:
        return list(self._connectors.values())

    def names(self) -> list[str]:
        return sorted(self._connectors)


registry = ConnectorRegistry()
registry.register(GreenhouseConnector())
registry.register(LeverConnector())
registry.register(AshbyConnector())
registry.register(WorkableConnector())
registry.register(RecruiteeConnector())
registry.register(PersonioConnector())
registry.register(RedditJobsConnector())
registry.register(WorkdayCrawlerConnector())
registry.register(SuccessFactorsCrawlerConnector())
registry.register(ICimsCrawlerConnector())
registry.register(TaleoCrawlerConnector())

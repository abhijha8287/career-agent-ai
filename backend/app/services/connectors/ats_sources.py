import html
import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.core.config import settings
from app.services.connectors.base import ConnectorJob, JobConnector


def _clean_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _join_location(*parts: Any) -> str | None:
    values = [_string(part) for part in parts if _string(part)]
    return ", ".join(values) if values else None


class MultiBoardConnector(JobConnector):
    timeout = httpx.Timeout(20.0)

    def __init__(self, boards: list[str] | None = None) -> None:
        self.boards = boards or []

    async def search(self, query: str, location: str | None, limit: int) -> list[ConnectorJob]:
        jobs = await self.fetch_all()
        query_lower = query.lower().strip()
        location_lower = location.lower().strip() if location else ""
        filtered = [
            job
            for job in jobs
            if (not query_lower or query_lower in f"{job.title} {job.original_description}".lower())
            and (not location_lower or location_lower in (job.location or "").lower())
        ]
        return filtered[:limit]


class GreenhouseConnector(MultiBoardConnector):
    name = "greenhouse"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.greenhouse_boards)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for board in self.boards:
                response = await client.get(
                    f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
                    params={"content": "true"},
                )
                response.raise_for_status()
                payload = response.json()
                company = payload.get("name") or board
                for item in payload.get("jobs", []):
                    location = (item.get("location") or {}).get("name")
                    departments = [department.get("name") for department in item.get("departments", [])]
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(item.get("id")),
                            title=_string(item.get("title")),
                            company=_string(company),
                            location=location,
                            apply_url=_string(item.get("absolute_url")),
                            original_description=_clean_html(item.get("content")),
                            employment_type="full_time",
                            company_details={"board": board, "departments": departments},
                            raw_payload=item,
                        )
                    )
        return jobs


class LeverConnector(MultiBoardConnector):
    name = "lever"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.lever_sites)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for site in self.boards:
                response = await client.get(f"https://api.lever.co/v0/postings/{site}", params={"mode": "json"})
                response.raise_for_status()
                for item in response.json():
                    categories = item.get("categories") or {}
                    lists = item.get("lists") or []
                    description = " ".join(_clean_html(section.get("content")) for section in lists)
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(item.get("id")),
                            title=_string(item.get("text")),
                            company=site,
                            location=categories.get("location"),
                            apply_url=_string(item.get("hostedUrl") or item.get("applyUrl")),
                            original_description=description or _clean_html(item.get("descriptionPlain")),
                            employment_type=(categories.get("commitment") or "full_time").lower().replace("-", "_"),
                            company_details={"site": site, "team": categories.get("team"), "department": categories.get("department")},
                            raw_payload=item,
                        )
                    )
        return jobs


class AshbyConnector(MultiBoardConnector):
    name = "ashby"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.ashby_boards)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for board in self.boards:
                response = await client.get(
                    f"https://api.ashbyhq.com/posting-api/job-board/{board}",
                    params={"includeCompensation": "true"},
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("jobs", []):
                    location = item.get("location")
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(item.get("id") or item.get("jobId")),
                            title=_string(item.get("title")),
                            company=board,
                            location=location,
                            apply_url=_string(item.get("jobUrl") or item.get("applyUrl")),
                            original_description=_clean_html(item.get("descriptionHtml") or item.get("descriptionPlain")),
                            employment_type="full_time",
                            company_details={"board": board, "department": item.get("department"), "team": item.get("team")},
                            raw_payload=item,
                        )
                    )
        return jobs


class WorkableConnector(MultiBoardConnector):
    name = "workable"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.workable_accounts)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for account in self.boards:
                response = await client.get(f"https://apply.workable.com/api/v1/widget/accounts/{account}")
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("jobs", []):
                    location = item.get("location") or {}
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(item.get("shortcode") or item.get("id")),
                            title=_string(item.get("title")),
                            company=_string(payload.get("name") or account),
                            location=_join_location(location.get("city"), location.get("region"), location.get("country")),
                            apply_url=_string(item.get("url") or item.get("application_url")),
                            original_description=_clean_html(item.get("description") or item.get("full_description")),
                            employment_type=_string(item.get("employment_type") or "full_time").lower().replace("-", "_"),
                            company_details={"account": account, "department": item.get("department")},
                            raw_payload=item,
                        )
                    )
        return jobs


class RecruiteeConnector(MultiBoardConnector):
    name = "recruitee"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.recruitee_companies)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for company in self.boards:
                response = await client.get(f"https://{company}.recruitee.com/api/offers")
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("offers", []):
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(item.get("id") or item.get("slug")),
                            title=_string(item.get("title")),
                            company=company,
                            location=_join_location(item.get("city"), item.get("country")),
                            apply_url=_string(item.get("careers_url") or item.get("url")),
                            original_description=_clean_html(item.get("description") or item.get("requirements")),
                            employment_type=_string(item.get("kind") or "full_time").lower().replace("-", "_"),
                            company_details={"company": company, "department": item.get("department")},
                            raw_payload=item,
                        )
                    )
        return jobs


class PersonioConnector(MultiBoardConnector):
    name = "personio"

    def __init__(self, boards: list[str] | None = None) -> None:
        super().__init__(boards or settings.personio_companies)

    async def fetch_all(self) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for company in self.boards:
                response = await client.get(f"https://{company}.jobs.personio.de/xml")
                response.raise_for_status()
                root = ET.fromstring(response.text)
                for item in root.findall(".//position"):
                    external_id = item.findtext("id") or item.findtext("job_id") or item.findtext("recruitingCategory")
                    title = item.findtext("name") or item.findtext("jobName")
                    description = " ".join(text for text in item.itertext())
                    jobs.append(
                        ConnectorJob(
                            source=self.name,
                            external_job_id=_string(external_id or title),
                            title=_string(title),
                            company=company,
                            location=_join_location(item.findtext("office"), item.findtext("city"), item.findtext("country")),
                            apply_url=_string(item.findtext("applyUrl") or f"https://{company}.jobs.personio.de/job/{external_id}"),
                            original_description=_clean_html(description),
                            employment_type=_string(item.findtext("employmentType") or "full_time").lower().replace("-", "_"),
                            company_details={"company": company, "department": item.findtext("department")},
                            raw_payload={child.tag: child.text for child in item},
                        )
                    )
        return jobs

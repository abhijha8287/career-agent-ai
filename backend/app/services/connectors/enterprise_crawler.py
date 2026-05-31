import hashlib
import json
import re
from collections.abc import Iterable
from typing import Any

from app.core.config import settings
from app.services.connectors.base import ConnectorJob, JobConnector


JOB_TITLE_KEYS = {"title", "jobtitle", "job_title", "name", "externaltitle"}
JOB_ID_KEYS = {"id", "jobid", "job_id", "requisitionid", "requisition_id", "reqid", "externaljobid"}
DESCRIPTION_KEYS = {"description", "jobdescription", "externaldescription", "job_description", "summary"}
LOCATION_KEYS = {"location", "locations", "primarylocation", "city", "joblocation"}
APPLY_KEYS = {"applyurl", "apply_url", "url", "externalpath", "joburl", "canonicalurl"}
SKILL_WORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "aws",
    "azure",
    "gcp",
    "sql",
    "postgresql",
    "kubernetes",
    "docker",
    "machine learning",
    "data science",
    "salesforce",
    "sap",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _flatten_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _flatten_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_dicts(item)


def _find_key(data: dict[str, Any], keys: set[str]) -> Any:
    for key, value in data.items():
        if key.replace("-", "").replace("_", "").lower() in keys:
            return value
    return None


def _location(value: Any) -> str | None:
    if isinstance(value, str):
        return _clean(value) or None
    if isinstance(value, list):
        parts = [_location(item) for item in value]
        return "; ".join(part for part in parts if part) or None
    if isinstance(value, dict):
        parts = [_clean(value.get(key)) for key in ("city", "state", "region", "country", "name", "displayName")]
        return ", ".join(part for part in parts if part) or None
    return None


def _absolute_url(base_url: str, value: Any, external_id: str) -> str:
    raw = _clean(value)
    if raw.startswith("http"):
        return raw
    if raw.startswith("/"):
        return f"{base_url.rstrip('/')}{raw}"
    return f"{base_url.rstrip('/')}/job/{external_id}"


def _skills(text: str) -> list[str]:
    lower = text.lower()
    return sorted({skill.title() for skill in SKILL_WORDS if skill in lower})


class EnterpriseCrawlerConnector(JobConnector):
    requires_browser_assist = True

    def __init__(self, name: str, career_urls: list[str]) -> None:
        self.name = name
        self.career_urls = career_urls

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

    async def fetch_all(self) -> list[ConnectorJob]:
        if not self.career_urls:
            return []
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Install Playwright and run `python -m playwright install chromium`.") from exc

        jobs: list[ConnectorJob] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            for career_url in self.career_urls:
                captured_payloads: list[Any] = []
                page = await context.new_page()

                async def capture_response(response: Any) -> None:
                    content_type = response.headers.get("content-type", "")
                    url = response.url.lower()
                    if "json" not in content_type and not any(token in url for token in ("job", "career", "requisition")):
                        return
                    try:
                        captured_payloads.append(await response.json())
                    except Exception:
                        return

                page.on("response", capture_response)
                await page.goto(career_url, wait_until="networkidle", timeout=45_000)
                await page.wait_for_timeout(2_000)
                for payload in captured_payloads:
                    jobs.extend(self._extract_jobs(career_url, payload))
                await page.close()
            await browser.close()
        return self._dedupe(jobs)

    def _extract_jobs(self, career_url: str, payload: Any) -> list[ConnectorJob]:
        extracted: list[ConnectorJob] = []
        for item in _flatten_dicts(payload):
            title = _clean(_find_key(item, JOB_TITLE_KEYS))
            if not title or len(title) > 250:
                continue
            description = _clean(_find_key(item, DESCRIPTION_KEYS)) or title
            external_id = _clean(_find_key(item, JOB_ID_KEYS)) or hashlib.sha256(
                f"{self.name}:{career_url}:{title}:{description[:100]}".encode()
            ).hexdigest()[:24]
            apply_url = _absolute_url(career_url, _find_key(item, APPLY_KEYS), external_id)
            location = _location(_find_key(item, LOCATION_KEYS))
            skill_list = _skills(f"{title} {description}")
            extracted.append(
                ConnectorJob(
                    source=self.name,
                    external_job_id=external_id,
                    title=title,
                    company=self._company_from_url(career_url),
                    location=location,
                    apply_url=apply_url,
                    original_description=description,
                    employment_type="full_time",
                    required_skills=skill_list,
                    preferred_skills=[],
                    company_details={"career_url": career_url, "crawler": "playwright_network"},
                    raw_payload=item,
                )
            )
        return extracted

    def _company_from_url(self, career_url: str) -> str:
        host = re.sub(r"^https?://", "", career_url).split("/", 1)[0]
        return host.split(".")[0].replace("-", " ").title()

    def _dedupe(self, jobs: list[ConnectorJob]) -> list[ConnectorJob]:
        seen: set[tuple[str, str, str, str]] = set()
        unique: list[ConnectorJob] = []
        for job in jobs:
            key = (job.source, job.external_job_id, job.company, job.apply_url)
            if key in seen:
                continue
            seen.add(key)
            unique.append(job)
        return unique


class WorkdayCrawlerConnector(EnterpriseCrawlerConnector):
    def __init__(self) -> None:
        super().__init__("workday", settings.workday_career_urls)


class SuccessFactorsCrawlerConnector(EnterpriseCrawlerConnector):
    def __init__(self) -> None:
        super().__init__("successfactors", settings.successfactors_career_urls)


class ICimsCrawlerConnector(EnterpriseCrawlerConnector):
    def __init__(self) -> None:
        super().__init__("icims", settings.icims_career_urls)


class TaleoCrawlerConnector(EnterpriseCrawlerConnector):
    def __init__(self) -> None:
        super().__init__("taleo", settings.taleo_career_urls)

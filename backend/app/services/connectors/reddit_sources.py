import html
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.services.connectors.base import ConnectorJob, JobConnector


BUDGET_PATTERNS = [
    re.compile(r"(?i)(?:budget|pay|rate|compensation|salary)\s*[:\-]?\s*([^\n\r]{1,80})"),
    re.compile(
        r"(?i)(?:USD|INR|EUR|GBP|AUD|CAD|\$|Rs\.?)\s?\d[\d,.]*"
        r"(?:\s?(?:-|to)\s?(?:USD|INR|EUR|GBP|AUD|CAD|\$|Rs\.?)?\s?\d[\d,.]*)?"
        r"(?:\s?/(?:hr|hour|day|week|month|project))?"
    ),
]

LOCATION_PATTERN = re.compile(r"(?i)(?:location|onsite|hybrid)\s*[:\-]?\s*([^\n\r]{1,80})")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_budget(title: str, description: str) -> str | None:
    text = f"{title}\n{description}"
    for pattern in BUDGET_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
    return None


def extract_location(title: str, description: str) -> str | None:
    text = f"{title}\n{description}"
    if re.search(r"(?i)\bremote\b", text):
        return "Remote"
    match = LOCATION_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def posted_date(created_utc: int | float | None) -> str | None:
    if not created_utc:
        return None
    return datetime.fromtimestamp(float(created_utc), UTC).isoformat()


def reddit_link(permalink: str | None, url: str | None) -> str:
    if permalink:
        return f"https://www.reddit.com{permalink}"
    return url or "https://www.reddit.com"


class RedditJobsConnector(JobConnector):
    name = "reddit"

    def __init__(self, subreddits: list[str] | None = None) -> None:
        self.subreddits = subreddits or settings.reddit_subreddits
        self._oauth_token: str | None = None

    async def fetch_all(self) -> list[ConnectorJob]:
        return await self.search(query="", location=None, limit=100)

    async def search(self, query: str, location: str | None, limit: int) -> list[ConnectorJob]:
        jobs: list[ConnectorJob] = []
        seen: set[str] = set()
        per_subreddit = max(15, min(75, limit // max(1, len(self.subreddits)) + 15))
        headers = {"User-Agent": settings.reddit_user_agent}
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), headers=headers, follow_redirects=True) as client:
            for subreddit in self.subreddits:
                subreddit_jobs: list[ConnectorJob] = []

                for fetcher in (self._fetch_oauth_posts, self._fetch_rss_posts, self._fetch_json_posts):
                    try:
                        subreddit_jobs = await fetcher(client, subreddit, per_subreddit)
                        if subreddit_jobs:
                            break
                    except Exception as exc:
                        errors.append(f"r/{subreddit} {fetcher.__name__}: {exc}")

                for job in subreddit_jobs:
                    if job.external_job_id in seen or not self._matches(job, query, location):
                        continue
                    seen.add(job.external_job_id)
                    jobs.append(job)
                    if len(jobs) >= limit:
                        return jobs

        if not jobs and errors:
            raise RuntimeError(
                "Reddit blocked public access and no OAuth/RSS fallback succeeded. "
                "Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET from a Reddit app. "
                f"Last errors: {' | '.join(errors[-4:])}"
            )
        return jobs

    async def _fetch_oauth_posts(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        limit: int,
    ) -> list[ConnectorJob]:
        token = await self._get_oauth_token(client)
        response = await client.get(
            f"https://oauth.reddit.com/r/{subreddit}/new",
            params={"limit": limit, "raw_json": 1},
            headers={"Authorization": f"Bearer {token}", "User-Agent": settings.reddit_user_agent},
        )
        response.raise_for_status()
        children = response.json().get("data", {}).get("children", [])
        return [self._to_job(subreddit, child.get("data", {})) for child in children if child.get("data")]

    async def _get_oauth_token(self, client: httpx.AsyncClient) -> str:
        if self._oauth_token:
            return self._oauth_token
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise RuntimeError("Reddit OAuth credentials are not configured")

        response = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            data={"grant_type": "client_credentials"},
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
            headers={"User-Agent": settings.reddit_user_agent},
        )
        response.raise_for_status()
        self._oauth_token = response.json()["access_token"]
        return self._oauth_token

    async def _fetch_rss_posts(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        limit: int,
    ) -> list[ConnectorJob]:
        response = await client.get(f"https://www.reddit.com/r/{subreddit}/new/.rss", params={"limit": limit})
        response.raise_for_status()
        root = ET.fromstring(response.text)
        return [self._rss_entry_to_job(subreddit, entry) for entry in root.findall("{http://www.w3.org/2005/Atom}entry")]

    async def _fetch_json_posts(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        limit: int,
    ) -> list[ConnectorJob]:
        last_error: Exception | None = None
        for host in ("https://www.reddit.com", "https://old.reddit.com"):
            try:
                response = await client.get(f"{host}/r/{subreddit}/new.json", params={"limit": limit, "raw_json": 1})
                response.raise_for_status()
                children = response.json().get("data", {}).get("children", [])
                return [self._to_job(subreddit, child.get("data", {})) for child in children if child.get("data")]
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        return []

    def _rss_entry_to_job(self, subreddit: str, entry: ET.Element) -> ConnectorJob:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        title = entry.findtext("atom:title", default="", namespaces=ns).strip()
        entry_id = entry.findtext("atom:id", default=title, namespaces=ns).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=ns).strip() or None
        content = strip_html(entry.findtext("atom:content", default="", namespaces=ns))
        author = entry.findtext("atom:author/atom:name", default="", namespaces=ns).strip() or None
        link_element = entry.find("atom:link", ns)
        link = link_element.attrib.get("href") if link_element is not None else entry_id
        budget = extract_budget(title, content)
        location = extract_location(title, content)

        return ConnectorJob(
            source=self.name,
            external_job_id=entry_id.rstrip("/").rsplit("/", 1)[-1] or entry_id,
            title=title,
            company=f"r/{subreddit}",
            location=location,
            apply_url=link,
            original_description=content or title,
            employment_type="freelance",
            company_details={
                "subreddit": subreddit,
                "author": author,
                "posted_date": updated,
                "budget": budget,
                "link": link,
                "feed": "rss",
            },
            raw_payload={"id": entry_id, "title": title, "content": content, "author": author, "updated": updated},
            budget=budget,
            author=author,
            posted_date=updated,
        )

    def _to_job(self, subreddit: str, data: dict[str, Any]) -> ConnectorJob:
        title = str(data.get("title") or "").strip()
        description = str(data.get("selftext") or "").strip()
        link = reddit_link(data.get("permalink"), data.get("url"))
        budget = extract_budget(title, description)
        location = extract_location(title, description)
        author = str(data.get("author") or "").strip() or None
        created = posted_date(data.get("created_utc"))

        return ConnectorJob(
            source=self.name,
            external_job_id=str(data.get("id") or link),
            title=title,
            company=f"r/{subreddit}",
            location=location,
            apply_url=link,
            original_description=description or title,
            employment_type="freelance",
            company_details={
                "subreddit": subreddit,
                "author": author,
                "posted_date": created,
                "budget": budget,
                "link": link,
                "score": data.get("score"),
                "num_comments": data.get("num_comments"),
                "feed": "oauth_or_json",
            },
            raw_payload=data,
            budget=budget,
            author=author,
            posted_date=created,
        )

    def _matches(self, job: ConnectorJob, query: str, location: str | None) -> bool:
        query_text = query.lower().strip()
        location_text = location.lower().strip() if location else ""
        haystack = f"{job.title} {job.original_description}".lower()
        return (not query_text or query_text in haystack) and (
            not location_text or location_text in (job.location or "").lower() or location_text in haystack
        )

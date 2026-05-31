import xml.etree.ElementTree as ET

from app.services.connectors.reddit_sources import RedditJobsConnector, extract_budget, extract_location, posted_date


def test_extract_budget_from_reddit_text() -> None:
    budget = extract_budget("[Hiring] Build a scraper", "Budget: $500 to $800 for the project")

    assert budget == "$500 to $800 for the project"


def test_extract_location_detects_remote() -> None:
    location = extract_location("[For Hire] Python developer", "Available for remote contract work.")

    assert location == "Remote"


def test_posted_date_is_iso_utc() -> None:
    assert posted_date(0) is None
    assert posted_date(1_700_000_000).startswith("2023-11-14T")


def test_reddit_post_maps_to_connector_job() -> None:
    connector = RedditJobsConnector(subreddits=["forhire"])
    job = connector._to_job(
        "forhire",
        {
            "id": "abc123",
            "title": "[Hiring] React dashboard",
            "selftext": "Budget: $1000. Remote only.",
            "author": "client_user",
            "created_utc": 1_700_000_000,
            "permalink": "/r/forhire/comments/abc123/react_dashboard/",
            "score": 12,
            "num_comments": 3,
        },
    )

    assert job.source == "reddit"
    assert job.external_job_id == "abc123"
    assert job.company == "r/forhire"
    assert job.employment_type == "freelance"
    assert job.budget == "$1000. Remote only."
    assert job.author == "client_user"
    assert job.apply_url == "https://www.reddit.com/r/forhire/comments/abc123/react_dashboard/"


def test_reddit_rss_entry_maps_to_connector_job() -> None:
    connector = RedditJobsConnector(subreddits=["forhire"])
    entry = ET.fromstring(
        """
        <entry xmlns="http://www.w3.org/2005/Atom">
          <id>https://www.reddit.com/r/forhire/comments/rss123/hiring_python_bot/</id>
          <title>[Hiring] Python bot</title>
          <updated>2026-05-31T10:00:00+00:00</updated>
          <author><name>rss_user</name></author>
          <link href="https://www.reddit.com/r/forhire/comments/rss123/hiring_python_bot/" />
          <content type="html">Budget: $300 remote job</content>
        </entry>
        """
    )

    job = connector._rss_entry_to_job("forhire", entry)

    assert job.source == "reddit"
    assert job.external_job_id == "hiring_python_bot"
    assert job.company == "r/forhire"
    assert job.budget == "$300 remote job"
    assert job.author == "rss_user"

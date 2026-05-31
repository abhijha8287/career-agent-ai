from app.services.connectors.enterprise_crawler import WorkdayCrawlerConnector


def test_enterprise_payload_extracts_jobs() -> None:
    connector = WorkdayCrawlerConnector()
    payload = {
        "jobPostings": [
            {
                "title": "Senior Python Engineer",
                "jobId": "WD-123",
                "description": "Build APIs with Python, React, and AWS.",
                "location": {"city": "Bengaluru", "country": "India"},
                "applyUrl": "/jobs/WD-123",
            }
        ]
    }

    jobs = connector._extract_jobs("https://acme.wd1.myworkdayjobs.com/careers", payload)

    assert len(jobs) == 1
    assert jobs[0].source == "workday"
    assert jobs[0].external_job_id == "WD-123"
    assert jobs[0].title == "Senior Python Engineer"
    assert jobs[0].location == "Bengaluru, India"
    assert "Python" in jobs[0].required_skills

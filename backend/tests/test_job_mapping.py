from app.services.connectors.base import ConnectorJob
from app.services.jobs_repository import _job_values


def test_job_values_uses_deduplication_fields() -> None:
    job = ConnectorJob(
        source="greenhouse",
        external_job_id="123",
        title="AI Engineer",
        company="Acme",
        location="Remote",
        apply_url="https://example.com/jobs/123",
        original_description="<p>Build AI systems</p>",
    )

    values = _job_values(job)

    assert values["source"] == "greenhouse"
    assert values["external_job_id"] == "123"
    assert values["company"] == "Acme"
    assert values["apply_url"] == "https://example.com/jobs/123"
    assert values["cleaned_description"] == "<p>Build AI systems</p>"

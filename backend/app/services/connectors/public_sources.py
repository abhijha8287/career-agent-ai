from app.services.connectors.base import ConnectorJob, JobConnector


class RemoteOkConnector(JobConnector):
    name = "remoteok"

    async def search(self, query: str, location: str | None, limit: int) -> list[ConnectorJob]:
        return [
            ConnectorJob(
                source=self.name,
                external_job_id=f"remoteok-{idx}",
                title=f"{query.title()} Engineer",
                company=f"Remote Company {idx}",
                location=location or "Remote",
                apply_url="https://remoteok.com",
                original_description=(
                    f"We are hiring a {query} engineer with Python, React, APIs, cloud, and product ownership."
                ),
                required_skills=["Python", "React", "APIs"],
                preferred_skills=["AWS", "PostgreSQL", "Celery"],
                responsibilities=["Build production features", "Collaborate with product", "Improve reliability"],
                benefits=["Remote work", "Flexible hours"],
                company_details={"industry": "SaaS", "size": "51-200", "tech_stack": ["Python", "React", "AWS"]},
            )
            for idx in range(1, min(limit, 5) + 1)
        ]


class AtsConnector(JobConnector):
    name = "public_ats"

    async def search(self, query: str, location: str | None, limit: int) -> list[ConnectorJob]:
        boards = ["greenhouse", "lever", "ashby", "smartrecruiters", "bamboohr"]
        jobs: list[ConnectorJob] = []
        for idx, board in enumerate(boards[:limit], start=1):
            jobs.append(
                ConnectorJob(
                    source=board,
                    external_job_id=f"{board}-{idx}",
                    title=f"{query.title()} Specialist",
                    company=f"{board.title()} Startup",
                    location=location or "Hybrid",
                    apply_url=f"https://{board}.io",
                    original_description=f"{board} posting for {query}. Requires ownership, communication, and delivery.",
                    required_skills=[query.title(), "Communication", "Execution"],
                    preferred_skills=["Analytics", "Automation"],
                    company_details={"funding": "Seed-Series B", "industry": "Technology"},
                )
            )
        return jobs

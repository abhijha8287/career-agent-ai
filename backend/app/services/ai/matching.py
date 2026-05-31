from app.services.connectors.base import ConnectorJob
from app.services.ai.embeddings import EmbeddingService, cosine_similarity


class MatchingService:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()

    def score(self, candidate: dict, job: ConnectorJob | dict) -> dict:
        required = set(self._skills(job, "required_skills"))
        preferred = set(self._skills(job, "preferred_skills"))
        candidate_skills = {skill.lower() for skill in candidate.get("skills", [])}
        normalized_required = {skill.lower() for skill in required}
        normalized_preferred = {skill.lower() for skill in preferred}

        candidate_text = self._candidate_text(candidate)
        job_text = self._job_text(job)
        semantic_score = int(cosine_similarity(self.embedding_service.embed(candidate_text), self.embedding_service.embed(job_text)) * 100)
        skill_score = self._skill_score(candidate_skills, normalized_required, normalized_preferred)
        experience_score = self._experience_score(candidate, job)
        location_score = 100 if self._location_fit(candidate, job) else 40
        match_score = round((semantic_score * 0.4) + (skill_score * 0.3) + (experience_score * 0.2) + (location_score * 0.1))
        gaps = sorted(skill for skill in required if skill.lower() not in candidate_skills)

        return {
            "match_score": match_score,
            "semantic_match_score": semantic_score,
            "skill_match_score": skill_score,
            "skill_gap": gaps,
            "location_fit_score": location_score,
            "experience_fit_score": experience_score,
            "rationale": "Final score = 40% semantic match + 30% skills + 20% experience + 10% location.",
        }

    def _skill_score(self, candidate_skills: set[str], required: set[str], preferred: set[str]) -> int:
        required_hits = len(candidate_skills & required)
        preferred_hits = len(candidate_skills & preferred)
        required_score = required_hits / max(1, len(required))
        preferred_score = preferred_hits / max(1, len(preferred)) if preferred else 1.0
        return int(((required_score * 0.75) + (preferred_score * 0.25)) * 100)

    def _skills(self, job: ConnectorJob | dict, key: str) -> list[str]:
        if isinstance(job, dict):
            return job.get(key, [])
        return getattr(job, key)

    def _location_fit(self, candidate: dict, job: ConnectorJob | dict) -> bool:
        location = job.get("location") if isinstance(job, dict) else job.location
        if not location:
            return True
        prefs = [item.lower() for item in candidate.get("preferred_locations", [])]
        return "remote" in location.lower() or any(pref in location.lower() for pref in prefs)

    def _experience_score(self, candidate: dict, job: ConnectorJob | dict) -> int:
        years = float(candidate.get("years_experience") or 0)
        text = self._job_text(job).lower()
        matches = [int(value) for value in __import__("re").findall(r"(\d+)\+?\s+years?", text)]
        required_years = min(matches) if matches else 0
        if required_years == 0:
            return 100
        if years >= required_years:
            return 100
        return max(20, int((years / required_years) * 100))

    def _candidate_text(self, candidate: dict) -> str:
        parts = [
            " ".join(candidate.get("skills", [])),
            " ".join(candidate.get("preferred_roles", [])),
            candidate.get("profile_summary") or "",
            candidate.get("resume_text") or "",
            str(candidate.get("years_experience") or ""),
        ]
        return " ".join(parts)

    def _job_text(self, job: ConnectorJob | dict) -> str:
        if isinstance(job, dict):
            parts = [
                job.get("title", ""),
                job.get("company", ""),
                job.get("cleaned_description", ""),
                job.get("original_description", ""),
                " ".join(job.get("required_skills", [])),
                " ".join(job.get("preferred_skills", [])),
                " ".join(job.get("responsibilities", [])),
            ]
        else:
            parts = [
                job.title,
                job.company,
                job.original_description,
                " ".join(job.required_skills),
                " ".join(job.preferred_skills),
                " ".join(job.responsibilities),
            ]
        return " ".join(str(part) for part in parts if part)

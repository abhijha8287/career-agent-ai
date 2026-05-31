from app.services.ai.matching import MatchingService


class StaticEmbeddingService:
    def embed(self, text: str) -> list[float]:
        if "python" in text.lower():
            return [1.0, 0.0]
        return [0.0, 1.0]


def test_weighted_ai_ranking_components() -> None:
    candidate = {
        "skills": ["Python", "React"],
        "preferred_locations": ["Remote"],
        "years_experience": 3,
        "resume_text": "Python React developer",
    }
    job = {
        "title": "Python Engineer",
        "company": "Acme",
        "required_skills": ["Python", "React", "AWS"],
        "preferred_skills": ["PostgreSQL"],
        "cleaned_description": "Python role requiring 5 years experience. Remote.",
        "location": "Remote",
    }

    score = MatchingService(embedding_service=StaticEmbeddingService()).score(candidate, job)

    assert score["semantic_match_score"] == 100
    assert score["skill_match_score"] == 50
    assert score["experience_fit_score"] == 60
    assert score["location_fit_score"] == 100
    assert score["match_score"] == 77

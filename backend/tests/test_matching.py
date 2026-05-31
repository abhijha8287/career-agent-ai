from app.services.ai.matching import MatchingService


def test_matching_identifies_skill_gap() -> None:
    candidate = {"skills": ["Python", "React"], "preferred_locations": ["Remote"], "salary_expectation": 100000}
    job = {
        "required_skills": ["Python", "React", "AWS"],
        "preferred_skills": ["PostgreSQL"],
        "location": "Remote",
        "salary_max": 120000,
    }

    score = MatchingService().score(candidate, job)

    assert score["match_score"] >= 60
    assert score["skill_gap"] == ["AWS"]

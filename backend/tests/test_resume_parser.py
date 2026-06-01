from app.services.resume_parser import extract_candidate_name, extract_skills, parse_resume, summarize_resume


def test_parse_text_resume_and_extract_skills() -> None:
    text = "Python developer with React, FastAPI, PostgreSQL, Docker, and AWS experience."

    parsed = parse_resume("resume.txt", text.encode())
    skills = extract_skills(parsed)

    assert "Python" in skills
    assert "React" in skills
    assert "Fastapi" in skills
    assert "Postgresql" in skills


def test_summarize_resume_compacts_text() -> None:
    summary = summarize_resume("Python\n\nReact\tAWS")

    assert summary == "Python React AWS"


def test_extract_candidate_name_from_top_of_resume() -> None:
    text = "Asha Patel\nasha@example.com\nPython developer with React experience"

    assert extract_candidate_name(text) == "Asha Patel"

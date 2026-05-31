from app.services.resume_parser import extract_skills, parse_resume, summarize_resume


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

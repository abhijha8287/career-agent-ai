from app.services.ai.materials import MaterialGenerationService
from app.services.pdf_generator import generate_document_pdf


def test_generates_three_resume_versions_with_keywords() -> None:
    candidate = {
        "full_name": "Asha Patel",
        "skills": ["Python", "React", "PostgreSQL"],
        "years_experience": 4,
        "resume_text": "Python React PostgreSQL engineer building APIs.",
        "profile_summary": "Full-stack engineer focused on reliable product delivery.",
    }
    job = {
        "title": "AI Product Engineer",
        "company": "Acme",
        "required_skills": ["Python", "React", "OpenAI"],
        "preferred_skills": ["PostgreSQL"],
        "cleaned_description": "Build AI product workflows with Python, React, OpenAI, and PostgreSQL.",
    }

    materials = MaterialGenerationService().generate(candidate, job)

    assert materials["ats_score"] > 70
    assert materials["keywords"]
    assert "python" in materials["matched_keywords"]
    assert len(materials["versions"]) == 3
    assert [version["label"] for version in materials["versions"]] == ["resume_v1", "resume_v2", "resume_v3"]
    assert "AI Product Engineer" in materials["cover_letter"]


def test_generates_downloadable_pdf_bytes() -> None:
    pdf = generate_document_pdf(
        "Asha Patel - Tailored Resume",
        "AI Product Engineer at Acme",
        "# Asha Patel\n\n## Professional Summary\nPython engineer\n\n- Built APIs with React and PostgreSQL.",
    )

    assert pdf.startswith(b"%PDF-1.4")
    assert b"/Type /Catalog" in pdf
    assert len(pdf) > 1000

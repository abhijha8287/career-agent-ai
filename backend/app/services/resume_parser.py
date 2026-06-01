from io import BytesIO
import re

from docx import Document
from pypdf import PdfReader


COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "celery",
    "machine learning",
    "deep learning",
    "nlp",
    "rag",
    "openai",
    "data science",
    "pandas",
    "spark",
}


def parse_resume(filename: str, content: bytes) -> str:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return _parse_pdf(content)
    if lowered.endswith(".docx"):
        return _parse_docx(content)
    return content.decode("utf-8", errors="ignore")


def extract_skills(text: str) -> list[str]:
    normalized = text.lower()
    found = {skill for skill in COMMON_SKILLS if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", normalized)}
    return sorted(skill.title() for skill in found)


def summarize_resume(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:500]


def extract_candidate_name(text: str, fallback: str = "Candidate") -> str:
    for raw_line in text.splitlines()[:12]:
        line = re.sub(r"\s+", " ", raw_line).strip(" -|•\t")
        lowered = line.lower()
        if not line or len(line) > 60:
            continue
        if any(token in lowered for token in ["@", "linkedin", "github", "resume", "curriculum", "phone", "email"]):
            continue
        if re.search(r"\d", line):
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(re.search(r"[A-Za-z]", word) for word in words):
            return " ".join(word[:1].upper() + word[1:] for word in words)
    return fallback


def _parse_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(content: bytes) -> str:
    document = Document(BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)

import re


STOPWORDS = {
    "about",
    "across",
    "after",
    "also",
    "and",
    "are",
    "build",
    "can",
    "for",
    "from",
    "have",
    "into",
    "our",
    "role",
    "team",
    "that",
    "the",
    "this",
    "with",
    "will",
    "work",
    "you",
    "your",
}


class MaterialGenerationService:
    def generate(self, candidate: dict, job: dict) -> dict:
        title = job.get("title") or "the role"
        company = job.get("company") or "the company"
        description = job.get("cleaned_description") or job.get("original_description") or ""
        resume_text = candidate.get("resume_text") or candidate.get("profile_summary") or ""
        skills = self._unique(candidate.get("skills", []))
        keywords = self.extract_keywords(job)
        matched_keywords = self._matched_keywords(keywords, skills, resume_text)
        missing_keywords = [keyword for keyword in keywords if keyword not in matched_keywords]
        ats_score = self._ats_score(keywords, matched_keywords)
        versions = [
            self._resume_version("resume_v1", "ATS baseline", candidate, title, company, skills, keywords, matched_keywords, missing_keywords),
            self._resume_version("resume_v2", "Keyword focused", candidate, title, company, skills, keywords, matched_keywords, missing_keywords[:8]),
            self._resume_version("resume_v3", "Recruiter ready", candidate, title, company, skills, keywords, matched_keywords, missing_keywords[:4]),
        ]
        cover = self._cover_letter(candidate, title, company, matched_keywords, description)
        required = ", ".join(keywords[:8]) or title

        return {
            "resume_markdown": versions[0]["resume_markdown"],
            "cover_letter": cover,
            "recruiter_message": f"Hi, I am interested in {title} at {company}. My background aligns with {required}.",
            "linkedin_message": f"Hi, I noticed {company} is hiring for {title}. I would love to connect and learn more.",
            "follow_up_email": f"Following up on my application for {title}. I remain very interested in {company}.",
            "ats_score": ats_score,
            "keywords": keywords,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "versions": versions,
        }

    def extract_keywords(self, job: dict) -> list[str]:
        seeded = []
        seeded.extend(job.get("required_skills") or [])
        seeded.extend(job.get("preferred_skills") or [])
        text = " ".join(
            [
                job.get("title") or "",
                job.get("cleaned_description") or job.get("original_description") or "",
                " ".join(job.get("responsibilities") or []),
            ]
        )
        words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{2,}", text)]
        scored: dict[str, int] = {}
        for raw in seeded + words:
            keyword = raw.strip().lower()
            if len(keyword) < 3 or keyword in STOPWORDS:
                continue
            scored[keyword] = scored.get(keyword, 0) + (3 if raw in seeded else 1)
        return [keyword for keyword, _ in sorted(scored.items(), key=lambda item: (-item[1], item[0]))[:18]]

    def _resume_version(
        self,
        label: str,
        focus: str,
        candidate: dict,
        title: str,
        company: str,
        skills: list[str],
        keywords: list[str],
        matched_keywords: list[str],
        missing_keywords: list[str],
    ) -> dict:
        name = candidate.get("full_name") or "Candidate"
        summary = candidate.get("profile_summary") or f"{title} candidate with relevant delivery experience."
        experience_years = candidate.get("years_experience") or 0
        emphasized = self._unique(matched_keywords + skills)[:14]
        resume = f"""# {name}

## Target Role
{title} at {company}

## Professional Summary
{summary}

This {focus.lower()} version positions the resume for {title} and emphasizes truthful evidence around: {", ".join(emphasized) or "role requirements"}.

## Core Skills
{", ".join(emphasized) or "Add verified skills from your resume"}

## Relevant Experience
- Delivered work aligned to {title} using {", ".join(emphasized[:6]) or "the required tools and practices"}.
- Communicated tradeoffs, shipped measurable outcomes, and adapted to team priorities.
- Brings {experience_years} years of relevant experience based on the uploaded resume profile.

## ATS Keywords Included
{", ".join(keywords[:14]) or "No JD keywords detected"}

## Keywords To Add Only If True
{", ".join(missing_keywords) or "No major keyword gaps detected"}

Optimization rule: emphasize only skills and experience already present in the uploaded resume. Do not fabricate employers, projects, dates, credentials, or metrics.
"""
        return {"label": label, "focus": focus, "resume_markdown": resume}

    def _cover_letter(self, candidate: dict, title: str, company: str, matched_keywords: list[str], description: str) -> str:
        name = candidate.get("full_name") or "Candidate"
        proof = ", ".join(matched_keywords[:6]) or "the role requirements"
        company_sentence = "I am especially interested in the scope described in the job posting."
        if description:
            company_sentence = "The role stood out because it connects directly to the kind of work I have been targeting."
        return (
            f"Dear {company} hiring team,\n\n"
            f"I am excited to apply for {title}. My resume aligns with the role through {proof}. "
            f"{company_sentence} I would welcome the chance to discuss how my experience can help your team deliver measurable outcomes.\n\n"
            "Sincerely,\n"
            f"{name}"
        )

    def _matched_keywords(self, keywords: list[str], skills: list[str], resume_text: str) -> list[str]:
        haystack = " ".join(skills + [resume_text]).lower()
        return [keyword for keyword in keywords if keyword.lower() in haystack]

    def _ats_score(self, keywords: list[str], matched_keywords: list[str]) -> int:
        if not keywords:
            return 70
        coverage = len(matched_keywords) / len(keywords)
        return min(98, max(45, int(55 + coverage * 43)))

    def _unique(self, items: list[str]) -> list[str]:
        seen = set()
        values = []
        for item in items:
            value = str(item).strip()
            key = value.lower()
            if value and key not in seen:
                values.append(value)
                seen.add(key)
        return values

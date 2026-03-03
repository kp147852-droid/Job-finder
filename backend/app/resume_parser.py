from __future__ import annotations

import re
from typing import List

from .models import ResumeData

COMMON_SKILLS = {
    "python",
    "sql",
    "excel",
    "javascript",
    "typescript",
    "react",
    "node",
    "aws",
    "docker",
    "kubernetes",
    "tableau",
    "power bi",
    "salesforce",
    "project management",
}


def _extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    skills = [skill for skill in COMMON_SKILLS if skill in lowered]
    return sorted(skills)


def _extract_years_experience(text: str) -> float:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s+years",
        r"(\d+(?:\.\d+)?)\+?\s+yrs",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1))
    return 0.0


def parse_resume_text(user_id: str, text: str) -> ResumeData:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    inferred_titles = [line for line in lines[:8] if len(line.split()) <= 5]

    return ResumeData(
        user_id=user_id,
        skills=_extract_skills(text),
        titles=inferred_titles[:5],
        years_experience=_extract_years_experience(text),
        education=[line for line in lines if "university" in line.lower() or "b.s." in line.lower()],
        raw_text=text,
    )

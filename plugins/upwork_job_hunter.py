"""Upwork job-analysis helpers.

This module intentionally does not scrape Upwork or submit proposals. It provides
local scoring and proposal drafting for job data obtained through permitted means.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict


DEFAULT_SKILLS = [
    "excel", "power bi", "sql", "python", "data analysis", "data cleaning",
    "dashboard", "tableau", "statistics", "reporting", "google sheets",
]

@dataclass
class JobScore:
    score: int
    label: str
    matched_skills: list[str]
    missing_skills: list[str]
    budget_signal: str
    notes: list[str]

    def to_dict(self):
        return asdict(self)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def score_job(title: str, description: str, skills: list[str] | None = None, budget: str = "") -> JobScore:
    text = _norm(f"{title} {description}")
    wanted = [s.strip().lower() for s in (skills or DEFAULT_SKILLS) if s.strip()]
    matched = [s for s in wanted if s in text]
    missing = [s for s in wanted if s not in text]
    score = min(100, 35 + min(45, len(matched) * 7))
    notes = []
    if title.strip():
        score += 10
    if len(description.strip()) >= 300:
        score += 5
        notes.append("Detailed job description")
    if budget.strip():
        score += 5
        notes.append("Budget information provided")
    score = min(100, score)
    label = "Excellent Match" if score >= 85 else "Good Match" if score >= 70 else "Possible" if score >= 55 else "Skip"
    budget_signal = budget.strip() or "Not provided"
    return JobScore(score, label, matched, missing, budget_signal, notes)


def draft_proposal(title: str, description: str, score: JobScore, freelancer_name: str = "") -> str:
    name = freelancer_name.strip() or "there"
    skills = ", ".join(score.matched_skills[:5]) or "data analysis"
    return (
        f"Hi {name},\n\n"
        f"I can help with your {title.strip() or 'data analysis project'}. "
        f"The requirements align well with my work in {skills}. "
        "I can clean and validate the data, build the requested analysis/dashboard, "
        "and provide clear business-ready insights.\n\n"
        "I would first review the source data and expected outputs, then confirm the "
        "delivery plan before starting. I can also share a concise summary of the key findings.\n\n"
        "Regards"
    )

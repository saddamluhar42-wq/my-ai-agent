from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Job:
    title: str
    description: str
    budget: str = ""
    url: str = ""
    client_info: str = ""


DEFAULT_SKILLS = (
    "excel", "power bi", "sql", "python", "pandas", "data analysis",
    "data cleaning", "dashboard", "tableau", "statistics", "reporting",
)


def build_search_plan(skills: list[str] | None = None, min_match: int = 70) -> dict[str, Any]:
    terms = [s.strip().lower() for s in (skills or DEFAULT_SKILLS) if s.strip()]
    return {
        "queries": [
            "data analyst", "excel data analysis", "power bi dashboard",
            "sql data analysis", "python pandas data analysis", "business analytics",
        ],
        "skills": terms,
        "min_match": max(0, min(100, int(min_match))),
        "requires_human_review": True,
    }


def analyze_job(job: Job, skills: list[str] | None = None) -> dict[str, Any]:
    text = f"{job.title}\n{job.description}".lower()
    wanted = [s.lower().strip() for s in (skills or DEFAULT_SKILLS) if s.strip()]
    matches = sorted({s for s in wanted if s in text})
    skill_score = min(60, round(len(matches) / max(1, len(wanted)) * 60))
    quality_terms = ("clear requirements", "deliverables", "deadline", "dashboard", "report")
    quality_score = min(20, sum(4 for term in quality_terms if term in text))
    budget_score = 10 if job.budget.strip() else 0
    client_score = 10 if job.client_info.strip() else 0
    score = min(100, skill_score + quality_score + budget_score + client_score)
    label = "Excellent Match" if score >= 85 else "Good Match" if score >= 70 else "Possible" if score >= 50 else "Skip"
    return {
        "job": asdict(job), "score": score, "label": label,
        "matched_skills": matches, "missing_skills": [s for s in wanted if s not in matches],
        "requires_review": True,
    }


def generate_proposal(job: Job, profile_summary: str, relevant_projects: str = "") -> str:
    profile_summary = profile_summary.strip()
    relevant_projects = relevant_projects.strip()
    if not profile_summary:
        raise ValueError("A short profile summary is required before generating a proposal.")
    return (
        f"Hi,\n\nI reviewed your project for {job.title.strip() or 'data analysis'} and can help with it. "
        "I focus on practical, accurate analysis with clean deliverables and clear business insights.\n\n"
        f"Relevant background: {profile_summary}\n"
        + (f"Relevant projects: {relevant_projects}\n" if relevant_projects else "")
        + "\nI can first review the source data, confirm the required outputs, and then deliver a clean analysis/report. "
        "I would be happy to clarify the expected dashboard, metrics, and deadline before starting.\n\n"
        "Regards"
    )

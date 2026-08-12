"""Upwork job-hunting helpers.

Uses only permitted/public data or user-provided job text. No credential scraping,
CAPTCHA bypass, or unattended proposal submission is implemented.
"""
from .job_hunter import Job, analyze_job, build_search_plan, generate_proposal

__all__ = ["Job", "analyze_job", "build_search_plan", "generate_proposal"]

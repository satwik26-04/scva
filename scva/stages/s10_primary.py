"""
Stage 10: Primary Source Detection.
Identifies secondary citations (reviews, surveys) used in place of original foundational papers.
"""
from __future__ import annotations

from ..models.citation import BibEntry


REVIEW_KEYWORDS = ["survey", "review", "overview", "progress", "advances", "systematic review"]


def run_stage_10(entries: list[BibEntry]) -> list[dict[str, str]]:
    """Flag entries that are review/survey papers."""
    secondary_alerts = []

    for entry in entries:
        title_lower = entry.title.lower()
        if any(kw in title_lower for kw in REVIEW_KEYWORDS):
            secondary_alerts.append({
                "key": entry.key,
                "title": entry.title,
                "reason": "Paper title indicates a review or survey paper.",
                "recommendation": "Ensure primary original research papers are cited alongside or instead of this review paper.",
            })

    return secondary_alerts

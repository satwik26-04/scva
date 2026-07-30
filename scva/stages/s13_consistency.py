"""
Stage 13: Consistency Audit.
Ensures every citation key exists in the .bib file and flags uncited/orphan entries.
"""
from __future__ import annotations

from ..models.citation import CitationGraph


def run_stage_13(graph: CitationGraph) -> dict[str, list[str]]:
    """Perform consistency audit across .bib entries and .tex citation occurrences."""
    uncited = list(graph.uncited_keys())
    missing = list(graph.missing_keys())

    return {
        "uncited_entries": uncited,
        "missing_keys": missing,
    }

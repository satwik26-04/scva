"""
Stage 9: Overcitation / Undercitation Detection.
Identifies citation clusters (e.g. 5+ citations in one sentence) or broad claims with a single citation.
"""
from __future__ import annotations

from ..models.citation import CitationGraph


def run_stage_09(graph: CitationGraph) -> list[dict[str, str]]:
    """Detect overcitation clusters or suspicious density anomalies."""
    alerts = []

    # Map sentences to their citation keys
    sentence_citations: dict[str, list[str]] = {}
    for key, occs in graph.occurrences.items():
        for occ in occs:
            sentence_citations.setdefault(occ.sentence, []).append(key)

    for sentence, keys in sentence_citations.items():
        if len(keys) >= 5:
            alerts.append({
                "type": "OVERCITATION",
                "sentence": sentence,
                "citation_count": str(len(keys)),
                "keys": ", ".join(keys),
                "recommendation": f"Sentence contains {len(keys)} citations in a single cluster. Consider trimming irrelevant citations.",
            })

    return alerts

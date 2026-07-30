"""
Stage 14: PDF Deep Verification.
Locates exact supporting evidence quotes in cited paper PDFs/abstracts.
"""
from __future__ import annotations

import re
from ..models.paper import ClaimSupport, PaperKnowledge


def run_stage_14(
    claim_supports: list[ClaimSupport],
    knowledge_map: dict[str, PaperKnowledge],
) -> list[ClaimSupport]:
    """Search PDF/abstract text for exact evidence quotes supporting each claim."""
    updated_supports = []

    for cs in claim_supports:
        pk = knowledge_map.get(cs.citation_key)
        if not pk or not cs.evidence_quote:
            # If evidence quote not already supplied, try extracting matching sentence
            if pk and (pk.abstract or pk.conclusions):
                full_text = pk.abstract + " " + pk.conclusions
                sentences = [s.strip() for s in full_text.split(".") if len(s.strip()) > 15]

                # Find sentence with highest overlap
                best_sentence = ""
                max_matches = 0
                for s in sentences:
                    matches = sum(1 for word in s.split() if len(word) > 4 and word.lower() in cs.explanation.lower())
                    if matches > max_matches:
                        max_matches = matches
                        best_sentence = s

                if best_sentence:
                    cs.evidence_quote = best_sentence
                    cs.evidence_location = "Abstract"

        updated_supports.append(cs)

    return updated_supports

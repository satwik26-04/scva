"""
Stage 6: Claim Extraction from Manuscript.
Extracts scientific assertions and maps them to supporting citation keys.
"""
from __future__ import annotations

import re
from ..models.citation import CitationGraph, CitationOccurrence
from ..models.paper import Claim


CLAIM_INDICATORS = [
    r"demonstrat(ed|es)",
    r"show(ed|n|s)",
    r"prov(ed|es|en)",
    r"finds?",
    r"found",
    r"indicat(ed|es)",
    r"propos(ed|es)",
    r"introduc(ed|es)",
    r"achiev(ed|es)",
    r"report(ed|s)",
    r"observ(ed|es)",
    r"establish(ed|es)",
]


def run_stage_06(graph: CitationGraph) -> list[Claim]:
    """Extract all claims associated with citations from the manuscript graph."""
    claims: list[Claim] = []
    claim_counter = 1

    pattern = re.compile("|".join(CLAIM_INDICATORS), re.IGNORECASE)

    for key, occs in graph.occurrences.items():
        for occ in occs:
            sentence = occ.sentence
            if not sentence:
                continue

            # Check if sentence contains a scientific claim indicator or is an attributed assertion
            has_claim_word = bool(pattern.search(sentence))

            claim_obj = Claim(
                claim_id=f"CLAIM-{claim_counter:03d}",
                text=sentence,
                claim_fragment=occ.nearby_claim or sentence,
                section=occ.section,
                citation_keys=[key],
                tex_file=occ.tex_file,
                line_number=occ.line_number,
                is_attributed=True,
            )
            claims.append(claim_obj)
            claim_counter += 1

    return claims

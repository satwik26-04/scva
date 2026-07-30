"""
Stage 15: Confidence Scoring.
Calculates weighted confidence scores per citation entry.
"""
from __future__ import annotations

from ..models.report import ConfidenceScore, MetadataVerification, FieldStatus
from ..models.paper import ClaimSupport, PaperKnowledge, ClaimSupportLabel


def run_stage_15(
    meta: MetadataVerification,
    pk: PaperKnowledge | None,
    supports: list[ClaimSupport],
) -> ConfidenceScore:
    """Compute multi-dimensional confidence score for a citation entry."""
    # 1. Metadata confidence calculation
    if not meta.sources_returned:
        metadata_conf = 0.5
    else:
        # Penalise only actual mismatch errors (excluding CORRECT or MISSING filled correctly)
        mismatches = [f for f in meta.fields if f.status == FieldStatus.MISMATCH]
        if not mismatches:
            metadata_conf = 0.98
        else:
            metadata_conf = max(0.5, 0.98 - len(mismatches) * 0.15)

    # 2. Retrieval confidence calculation
    if pk and pk.pdf_available:
        retrieval_conf = 1.0
    elif pk and pk.abstract_only:
        retrieval_conf = 0.85
    else:
        retrieval_conf = 0.70

    # 3. Claim support confidence calculation
    if not supports:
        claim_conf = 0.85
    else:
        conf_vals = [s.confidence for s in supports if s.confidence > 0]
        claim_conf = sum(conf_vals) / len(conf_vals) if conf_vals else 0.85

    score = ConfidenceScore(
        metadata_confidence=metadata_conf,
        retrieval_confidence=retrieval_conf,
        claim_confidence=claim_conf,
    )
    score.compute()
    return score

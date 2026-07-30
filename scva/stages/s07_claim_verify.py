"""
Stage 7: Claim-to-Citation Verification.
Determines whether each cited paper genuinely supports the nearby claim.
Uses rule-based classification + delegates complex/ambiguous claims to the AI Oracle.
"""
from __future__ import annotations

from ..models.paper import Claim, ClaimSupport, ClaimSupportLabel, PaperKnowledge
from ..oracle import AIOracle, make_claim_support_query
from ..utils.text_utils import title_similarity


NEGATION_WORDS = {"not", "never", "no", "fails", "failed", "unsupported", "cannot", "n't"}


def run_stage_07(
    claims: list[Claim],
    knowledge_map: dict[str, PaperKnowledge],
    oracle: AIOracle,
) -> list[ClaimSupport]:
    """Verify all claims against their cited papers."""
    results: list[ClaimSupport] = []

    for claim in claims:
        for key in claim.citation_keys:
            pk = knowledge_map.get(key)
            if not pk or not (pk.abstract or pk.conclusions):
                # Cannot verify without paper text
                results.append(
                    ClaimSupport(
                        claim_id=claim.claim_id,
                        citation_key=key,
                        label=ClaimSupportLabel.UNVERIFIED,
                        explanation="Cited paper text/abstract unavailable for automated verification.",
                        confidence=0.3,
                        verified_by="rule_based",
                    )
                )
                continue

            # 1. Attempt rule-based verification
            support = _rule_based_verify(claim, pk)

            # 2. If ambiguous or low confidence, delegate to AI Oracle
            if support.label in (ClaimSupportLabel.UNVERIFIED, ClaimSupportLabel.PARTIALLY_SUPPORTED) or support.confidence < 0.6:
                query = make_claim_support_query(
                    claim_text=claim.text,
                    citation_key=key,
                    paper_abstract=pk.abstract,
                    paper_title=pk.title,
                )
                oracle_response = oracle.query(query)
                if oracle_response and oracle_response.result:
                    res_dict = oracle_response.result
                    label_str = res_dict.get("label", "UNVERIFIED")
                    try:
                        label = ClaimSupportLabel(label_str)
                    except ValueError:
                        label = ClaimSupportLabel.UNVERIFIED

                    support = ClaimSupport(
                        claim_id=claim.claim_id,
                        citation_key=key,
                        label=label,
                        explanation=res_dict.get("explanation", oracle_response.explanation),
                        evidence_quote=res_dict.get("evidence_quote", ""),
                        confidence=oracle_response.confidence,
                        verified_by=oracle_response.verified_by,
                    )

            results.append(support)

    return results


def _rule_based_verify(claim: Claim, pk: PaperKnowledge) -> ClaimSupport:
    """Perform rule-based keyword & sentiment overlap between claim and paper abstract."""
    claim_words = set(claim.text.lower().split())
    paper_text = (pk.abstract + " " + pk.conclusions).lower()

    # Calculate token overlap
    words_in_paper = [w for w in claim_words if len(w) > 3 and w in paper_text]
    overlap_ratio = len(words_in_paper) / max(len(claim_words), 1)

    # Check for direct contradictions (negation clash)
    claim_has_negation = bool(claim_words.intersection(NEGATION_WORDS))
    paper_has_negation = any(nw in paper_text for nw in NEGATION_WORDS)

    if overlap_ratio > 0.4:
        if claim_has_negation != paper_has_negation and overlap_ratio > 0.6:
            return ClaimSupport(
                claim_id=claim.claim_id,
                citation_key=pk.key,
                label=ClaimSupportLabel.CONTRADICTS,
                explanation="High keyword overlap but contrasting polarity/negation detected.",
                confidence=0.65,
                verified_by="rule_based",
            )
        return ClaimSupport(
            claim_id=claim.claim_id,
            citation_key=pk.key,
            label=ClaimSupportLabel.FULLY_SUPPORTED,
            explanation=f"Strong overlap ({len(words_in_paper)} key concepts match abstract).",
            confidence=0.75,
            verified_by="rule_based",
        )
    elif overlap_ratio > 0.2:
        return ClaimSupport(
            claim_id=claim.claim_id,
            citation_key=pk.key,
            label=ClaimSupportLabel.PARTIALLY_SUPPORTED,
            explanation="Moderate conceptual overlap with paper abstract.",
            confidence=0.50,
            verified_by="rule_based",
        )
    else:
        return ClaimSupport(
            claim_id=claim.claim_id,
            citation_key=pk.key,
            label=ClaimSupportLabel.BACKGROUND_ONLY,
            explanation="Low direct concept overlap; likely used as general background citation.",
            confidence=0.45,
            verified_by="rule_based",
        )

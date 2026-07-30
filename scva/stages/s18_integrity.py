"""
Stage 18: Scientific Integrity Quality Scoring.
Generates top-level manuscript quality summary metrics and scores.
"""
from __future__ import annotations

from ..models.report import EntryReport, IntegritySummary
from ..models.paper import ClaimSupportLabel


def run_stage_18(
    entry_reports: list[EntryReport],
    missing_citations: list[dict],
    consistency: dict[str, list[str]],
) -> IntegritySummary:
    """Compute aggregate scientific integrity summary scores."""
    summary = IntegritySummary(
        total_references=len(entry_reports),
        verified_count=sum(1 for r in entry_reports if r.confidence.overall >= 0.8),
        corrected_count=sum(1 for r in entry_reports if r.metadata.has_errors()),
        metadata_error_count=sum(len(r.metadata.errors()) for r in entry_reports),
        duplicate_references=sum(1 for r in entry_reports if r.is_duplicate),
        unused_references=len(consistency.get("uncited_entries", [])),
        missing_citations=len(missing_citations),
    )

    # Count field-specific metadata errors
    for r in entry_reports:
        for err in r.metadata.errors():
            fname = err.field_name
            if fname == "year":
                summary.wrong_year += 1
            elif fname == "pages":
                summary.wrong_pages += 1
            elif fname == "venue":
                summary.wrong_venue += 1
            elif fname == "authors":
                summary.wrong_authors += 1
            elif fname == "doi":
                summary.wrong_doi += 1

        # Count claim mismatches
        for cs in r.claim_supports:
            if cs.label == ClaimSupportLabel.DOES_NOT_SUPPORT:
                summary.unsupported_claims += 1
                summary.claim_mismatch_count += 1
            elif cs.label == ClaimSupportLabel.CONTRADICTS:
                summary.contradicted_claims += 1
                summary.claim_mismatch_count += 1

    summary.compute_scores()
    return summary

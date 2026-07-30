"""
Stage 16: Per-Entry Verification Report Generation.
Compiles metadata, claim support, confidence, and recommendations into EntryReport objects.
"""
from __future__ import annotations

from ..models.citation import BibEntry
from ..models.paper import ClaimSupport, PaperKnowledge
from ..models.report import (
    ConfidenceScore, DuplicateInfo, EntryReport, MetadataVerification, VersionInfo
)
from ..utils.bib_parser import bib_entry_to_string


def run_stage_16(
    entry: BibEntry,
    corrected_entry: BibEntry,
    meta: MetadataVerification,
    pk: PaperKnowledge | None,
    supports: list[ClaimSupport],
    confidence: ConfidenceScore,
    dup_info: DuplicateInfo | None,
    ver_info: VersionInfo | None,
    is_uncited: bool,
) -> EntryReport:
    """Compile entry report."""
    recs: list[str] = []

    if meta.has_errors():
        recs.append(f"Correct metadata errors: {len(meta.errors())} mismatch(es) found.")

    if dup_info:
        recs.append(f"Remove duplicate entry (duplicate of '{dup_info.duplicate_of}').")

    if ver_info and ver_info.recommended_version != ver_info.current_version:
        recs.append(f"Update venue: {ver_info.note}")

    if is_uncited:
        recs.append("Entry present in .bib but never cited in manuscript.")

    corrected_bib = bib_entry_to_string(corrected_entry)

    return EntryReport(
        key=entry.key,
        metadata=meta,
        claim_supports=supports,
        confidence=confidence,
        is_duplicate=bool(dup_info),
        duplicate_info=dup_info,
        version_info=ver_info,
        is_uncited=is_uncited,
        corrected_bib=corrected_bib,
        pdf_retrieved=bool(pk and pk.pdf_available),
        abstract_retrieved=bool(pk and (pk.abstract or pk.pdf_available)),
        recommendations=recs,
    )

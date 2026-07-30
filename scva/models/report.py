"""
Report models — per-entry and aggregate results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .paper import ClaimSupport, ClaimSupportLabel


class FieldStatus(str, Enum):
    CORRECT   = "CORRECT"
    CORRECTED = "CORRECTED"
    MISMATCH  = "MISMATCH"
    MISSING   = "MISSING"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class FieldVerification:
    field_name: str
    bib_value: str
    verified_value: str
    status: FieldStatus
    source: str = ""          # which API source provided the verified value
    note: str = ""


@dataclass
class MetadataVerification:
    key: str
    fields: list[FieldVerification] = field(default_factory=list)
    sources_queried: list[str] = field(default_factory=list)
    sources_returned: list[str] = field(default_factory=list)

    def errors(self) -> list[FieldVerification]:
        return [f for f in self.fields
                if f.status in (FieldStatus.MISMATCH, FieldStatus.CORRECTED)]

    def has_errors(self) -> bool:
        return bool(self.errors())


@dataclass
class DuplicateInfo:
    duplicate_of: str       # the other key
    reason: str             # "same_doi" | "same_title" | "same_key"


@dataclass
class VersionInfo:
    key: str
    current_version: str    # "arxiv" | "conference" | "journal"
    recommended_version: str
    note: str = ""


@dataclass
class ConfidenceScore:
    metadata_confidence: float = 0.0     # 0–1
    retrieval_confidence: float = 0.0    # 0–1
    claim_confidence: float = 0.0        # 0–1
    overall: float = 0.0

    def compute(self) -> None:
        self.overall = (
            0.4 * self.metadata_confidence
            + 0.3 * self.retrieval_confidence
            + 0.3 * self.claim_confidence
        )

    def label(self) -> str:
        if self.overall >= 0.85:
            return "HIGH"
        if self.overall >= 0.60:
            return "MEDIUM"
        return "LOW"


@dataclass
class EntryReport:
    """Full verification report for a single BibTeX entry."""
    key: str
    metadata: MetadataVerification
    claim_supports: list[ClaimSupport] = field(default_factory=list)
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)
    is_duplicate: bool = False
    duplicate_info: Optional[DuplicateInfo] = None
    version_info: Optional[VersionInfo] = None
    is_uncited: bool = False
    corrected_bib: str = ""     # corrected BibTeX snippet
    pdf_retrieved: bool = False
    abstract_retrieved: bool = False
    recommendations: list[str] = field(default_factory=list)

    def overall_status(self) -> str:
        if self.metadata.has_errors():
            return "ERRORS_FOUND"
        if any(cs.label == ClaimSupportLabel.CONTRADICTS
               for cs in self.claim_supports):
            return "CLAIM_CONTRADICTED"
        if any(cs.label == ClaimSupportLabel.DOES_NOT_SUPPORT
               for cs in self.claim_supports):
            return "CLAIM_UNSUPPORTED"
        return "OK"


@dataclass
class IntegritySummary:
    total_references: int = 0
    verified_count: int = 0
    corrected_count: int = 0
    metadata_error_count: int = 0
    wrong_year: int = 0
    wrong_pages: int = 0
    wrong_venue: int = 0
    wrong_authors: int = 0
    wrong_doi: int = 0
    claim_mismatch_count: int = 0
    unsupported_claims: int = 0
    contradicted_claims: int = 0
    missing_citations: int = 0
    duplicate_references: int = 0
    unused_references: int = 0
    broken_urls: int = 0
    bibliography_quality_score: float = 0.0
    citation_quality_score: float = 0.0
    publication_readiness_score: float = 0.0

    def compute_scores(self) -> None:
        n = max(self.total_references, 1)
        # Bibliography quality: penalise metadata errors and duplicates
        self.bibliography_quality_score = max(
            0.0,
            1.0 - (self.metadata_error_count / n) * 0.6
                - (self.duplicate_references / n) * 0.2
                - (self.broken_urls / n) * 0.2
        )
        # Citation quality: penalise unsupported / contradicted claims
        total_claims = max(
            self.unsupported_claims + self.contradicted_claims + self.verified_count, 1
        )
        self.citation_quality_score = max(
            0.0,
            1.0 - (self.unsupported_claims / total_claims) * 0.5
                - (self.contradicted_claims / total_claims) * 1.0
        )
        self.publication_readiness_score = (
            0.6 * self.bibliography_quality_score
            + 0.4 * self.citation_quality_score
        )


@dataclass
class FinalReport:
    entries: list[EntryReport] = field(default_factory=list)
    integrity: IntegritySummary = field(default_factory=IntegritySummary)
    ai_queries_pending: int = 0
    run_id: str = ""
    input_tex: str = ""
    input_bib: str = ""
    scva_version: str = "1.0.0"

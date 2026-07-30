"""
models package — expose everything from one import.
"""
from .citation import Author, BibEntry, CitationOccurrence, CitationGraph
from .paper import PaperKnowledge, Claim, ClaimSupport, ClaimSupportLabel
from .report import (
    FieldStatus, FieldVerification, MetadataVerification,
    DuplicateInfo, VersionInfo, ConfidenceScore,
    EntryReport, IntegritySummary, FinalReport,
)

__all__ = [
    "Author", "BibEntry", "CitationOccurrence", "CitationGraph",
    "PaperKnowledge", "Claim", "ClaimSupport", "ClaimSupportLabel",
    "FieldStatus", "FieldVerification", "MetadataVerification",
    "DuplicateInfo", "VersionInfo", "ConfidenceScore",
    "EntryReport", "IntegritySummary", "FinalReport",
]

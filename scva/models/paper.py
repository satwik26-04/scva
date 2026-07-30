"""
Paper knowledge and claim models.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClaimSupportLabel(str, Enum):
    FULLY_SUPPORTED    = "FULLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INDIRECT_SUPPORT   = "INDIRECT_SUPPORT"
    BACKGROUND_ONLY    = "BACKGROUND_ONLY"
    DOES_NOT_SUPPORT   = "DOES_NOT_SUPPORT"
    CONTRADICTS        = "CONTRADICTS"
    UNVERIFIED         = "UNVERIFIED"   # pending AI review


@dataclass
class PaperKnowledge:
    """Structured knowledge extracted from a cited paper."""
    key: str
    title: str = ""
    abstract: str = ""
    problem: str = ""
    method: str = ""
    dataset: str = ""
    contributions: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    conclusions: str = ""
    keywords: list[str] = field(default_factory=list)

    # Source metadata
    pdf_available: bool = False
    abstract_only: bool = False
    source_url: str = ""


@dataclass
class Claim:
    """A scientific claim extracted from the user's manuscript."""
    claim_id: str
    text: str                           # full sentence
    claim_fragment: str = ""            # the actual assertion
    section: str = ""
    citation_keys: list[str] = field(default_factory=list)
    tex_file: str = ""
    line_number: int = 0
    is_attributed: bool = True          # False = claim with no citation


@dataclass
class ClaimSupport:
    """Relationship between one claim and one cited paper."""
    claim_id: str
    citation_key: str
    label: ClaimSupportLabel = ClaimSupportLabel.UNVERIFIED
    explanation: str = ""
    evidence_quote: str = ""            # verbatim text from cited paper
    evidence_location: str = ""         # e.g. "Abstract, sentence 2"
    confidence: float = 0.0
    verified_by: str = "rule_based"     # "rule_based" | "ai_oracle" | "human"

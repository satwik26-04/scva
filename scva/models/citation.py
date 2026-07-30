"""
Data models for BibTeX entries and citation occurrences.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Author:
    """Normalised author representation."""
    given: str = ""
    family: str = ""
    raw: str = ""          # original string from the bib

    def full_name(self) -> str:
        if self.given and self.family:
            return f"{self.given} {self.family}"
        return self.raw or self.family or self.given

    def initials_name(self) -> str:
        """Produce 'J. Smith' style."""
        if self.given and self.family:
            initials = ". ".join(p[0] for p in self.given.split()) + "."
            return f"{initials} {self.family}"
        return self.full_name()

    def __str__(self) -> str:
        return self.full_name()


@dataclass
class BibEntry:
    """Represents a single BibTeX bibliography entry."""
    key: str
    entry_type: str                        # article, inproceedings, etc.
    title: str = ""
    authors: list[Author] = field(default_factory=list)
    year: Optional[str] = None
    venue: str = ""                        # journal / booktitle
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None
    isbn: Optional[str] = None
    edition: Optional[str] = None
    note: Optional[str] = None

    # raw fields dict preserved for round-trip BibTeX output
    raw_fields: dict[str, str] = field(default_factory=dict)

    def author_string(self) -> str:
        return " and ".join(a.full_name() for a in self.authors)

    def is_arxiv_only(self) -> bool:
        return (
            self.entry_type in ("misc", "unpublished")
            or "arxiv" in (self.venue or "").lower()
            or (self.arxiv_id is not None and not self.doi)
        )


@dataclass
class CitationOccurrence:
    """One in-text citation occurrence."""
    key: str                        # BibTeX key
    tex_file: str                   # source .tex file path
    line_number: int = 0
    section: str = ""
    subsection: str = ""
    sentence: str = ""              # full sentence containing the citation
    paragraph: str = ""             # surrounding paragraph text
    nearby_claim: str = ""          # extracted claim near this citation


@dataclass
class CitationGraph:
    """Maps citation keys to their occurrences and BibTeX entries."""
    entries: dict[str, BibEntry] = field(default_factory=dict)
    occurrences: dict[str, list[CitationOccurrence]] = field(default_factory=dict)

    def all_keys(self) -> set[str]:
        return set(self.entries.keys())

    def cited_keys(self) -> set[str]:
        return set(self.occurrences.keys())

    def uncited_keys(self) -> set[str]:
        return self.all_keys() - self.cited_keys()

    def missing_keys(self) -> set[str]:
        """Keys cited in text but absent from the bib."""
        return self.cited_keys() - self.all_keys()

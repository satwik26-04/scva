"""
Base class and interface for metadata source integrations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import aiohttp

from ..models.citation import Author


@dataclass
class SourceRecord:
    """Standardized result returned by a metadata source."""
    source_name: str
    doi: Optional[str] = None
    title: str = ""
    authors: list[Author] = field(default_factory=list)
    venue: str = ""
    year: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    arxiv_id: Optional[str] = None
    abstract: str = ""
    raw_response: dict = field(default_factory=dict)


class MetadataSource(ABC):
    """Abstract base class for academic metadata API providers."""

    name: str = "base"
    reliability_weight: float = 0.5  # Weight in multi-source consensus (0.0 to 1.0)

    @abstractmethod
    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        """Fetch metadata by DOI."""
        pass

    @abstractmethod
    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        """Search metadata by title and optional author hint."""
        pass

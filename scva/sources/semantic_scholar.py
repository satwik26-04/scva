"""
Semantic Scholar REST API integration.
"""
from __future__ import annotations

from typing import Optional
import aiohttp

from .base import MetadataSource, SourceRecord
from ..models.citation import Author
from ..utils.async_utils import fetch_json


class SemanticScholarSource(MetadataSource):
    name = "SemanticScholar"
    reliability_weight = 0.85

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper"
    FIELDS = "title,authors,venue,year,volume,issue,pages,externalIds,abstract,url,publicationTypes"

    def _get_headers(self) -> dict[str, str]:
        from ..config import ConfigManager
        key = ConfigManager().get_key("semantic_scholar")
        return {"x-api-key": key} if key else {}

    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        clean_doi = doi.strip()
        url = f"{self.BASE_URL}/DOI:{clean_doi}"
        params = {"fields": self.FIELDS}
        resp = await fetch_json(session, url, params=params, headers=self._get_headers())
        if not resp:
            return None
        return self._parse_paper(resp)

    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        url = f"{self.BASE_URL}/search"
        params = {"query": title, "limit": 1, "fields": self.FIELDS}
        resp = await fetch_json(session, url, params=params, headers=self._get_headers())
        if not resp:
            return None
        data = resp.get("data", [])
        if not data:
            return None
        return self._parse_paper(data[0])

    def _parse_paper(self, paper: dict) -> SourceRecord:
        title = paper.get("title", "")

        authors: list[Author] = []
        for a in paper.get("authors", []):
            name = a.get("name", "")
            parts = name.split()
            if len(parts) >= 2:
                authors.append(Author(given=" ".join(parts[:-1]), family=parts[-1], raw=name))
            else:
                authors.append(Author(given="", family=name, raw=name))

        venue = paper.get("venue", "")
        year = str(paper.get("year", "")) if paper.get("year") else None

        ext_ids = paper.get("externalIds", {}) or {}
        doi = ext_ids.get("DOI")
        arxiv_id = ext_ids.get("ArXiv")

        abstract = paper.get("abstract", "") or ""

        return SourceRecord(
            source_name=self.name,
            doi=doi,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            pages=paper.get("pages"),
            url=paper.get("url"),
            arxiv_id=arxiv_id,
            abstract=abstract,
            raw_response=paper,
        )

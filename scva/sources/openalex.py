"""
OpenAlex REST API integration.
"""
from __future__ import annotations

from typing import Optional
import aiohttp

from .base import MetadataSource, SourceRecord
from ..models.citation import Author
from ..utils.async_utils import fetch_json


class OpenAlexSource(MetadataSource):
    name = "OpenAlex"
    reliability_weight = 0.90  # Comprehensive open scientific graph

    BASE_URL = "https://api.openalex.org/works"

    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        clean_doi = doi.strip()
        url = f"{self.BASE_URL}/https://doi.org/{clean_doi}"
        resp = await fetch_json(session, url)
        if not resp:
            return None
        return self._parse_work(resp)

    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        params = {"search": title, "per-page": 1}
        resp = await fetch_json(session, self.BASE_URL, params=params)
        if not resp:
            return None
        results = resp.get("results", [])
        if not results:
            return None
        return self._parse_work(results[0])

    def _parse_work(self, work: dict) -> SourceRecord:
        title = work.get("display_name", "") or work.get("title", "")

        # Authors
        authors: list[Author] = []
        for ship in work.get("authorships", []):
            name = ship.get("author", {}).get("display_name", "")
            parts = name.split()
            if len(parts) >= 2:
                authors.append(Author(given=" ".join(parts[:-1]), family=parts[-1], raw=name))
            else:
                authors.append(Author(given="", family=name, raw=name))

        # Venue / Primary location
        primary_loc = work.get("primary_location", {}) or {}
        source = primary_loc.get("source", {}) or {}
        venue = source.get("display_name", "")

        year = str(work.get("publication_year", "")) if work.get("publication_year") else None

        biblio = work.get("biblio", {})
        volume = biblio.get("volume")
        issue = biblio.get("issue")
        first_page = biblio.get("first_page")
        last_page = biblio.get("last_page")
        pages = f"{first_page}-{last_page}" if first_page and last_page else first_page

        doi_url = work.get("doi", "")
        doi = doi_url.replace("https://doi.org/", "") if doi_url else None

        # Abstract inverted index reconstruction
        abstract = ""
        inv_idx = work.get("abstract_inverted_index")
        if inv_idx:
            word_positions = []
            for word, positions in inv_idx.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort(key=lambda x: x[0])
            abstract = " ".join(w for _, w in word_positions)

        return SourceRecord(
            source_name=self.name,
            doi=doi,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            volume=volume,
            number=issue,
            pages=pages,
            url=doi_url or work.get("id"),
            abstract=abstract,
            raw_response=work,
        )

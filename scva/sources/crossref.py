"""
Crossref REST API integration.
"""
from __future__ import annotations

from typing import Optional
import aiohttp

from .base import MetadataSource, SourceRecord
from ..models.citation import Author
from ..utils.async_utils import fetch_json


class CrossrefSource(MetadataSource):
    name = "Crossref"
    reliability_weight = 1.0  # Primary authoritative source for DOIs

    BASE_URL = "https://api.crossref.org/works"

    def _get_headers(self) -> dict[str, str]:
        from ..config import ConfigManager
        mailto = ConfigManager().get_key("crossref_mailto") or "scva-polite@research.org"
        return {"User-Agent": f"SCVA/1.0 (mailto:{mailto})"}

    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        clean_doi = doi.strip()
        url = f"{self.BASE_URL}/{clean_doi}"
        resp = await fetch_json(session, url, headers=self._get_headers())
        if not resp or resp.get("status") != "ok":
            return None
        return self._parse_message(resp.get("message", {}))

    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        query = f"{title} {author_hint}".strip()
        params = {"query.title": title, "rows": 1}
        resp = await fetch_json(session, self.BASE_URL, params=params)
        if not resp or resp.get("status") != "ok":
            return None
        items = resp.get("message", {}).get("items", [])
        if not items:
            return None
        return self._parse_message(items[0])

    def _parse_message(self, msg: dict) -> SourceRecord:
        # Title
        titles = msg.get("title", [])
        title = titles[0] if titles else ""

        # Authors
        authors: list[Author] = []
        for a in msg.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            authors.append(Author(given=given, family=family, raw=f"{given} {family}".strip()))

        # Container / Venue
        containers = msg.get("container-title", [])
        venue = containers[0] if containers else ""

        # Dates / Year
        year = None
        for date_key in ("published-print", "published-online", "created", "issued"):
            date_parts = msg.get(date_key, {}).get("date-parts", [[]])
            if date_parts and date_parts[0] and date_parts[0][0]:
                year = str(date_parts[0][0])
                break

        # Page range
        page = msg.get("page")

        # Volume / Issue
        volume = msg.get("volume")
        issue = msg.get("issue")

        # DOI & Publisher
        doi = msg.get("DOI")
        publisher = msg.get("publisher")
        url = msg.get("URL")

        return SourceRecord(
            source_name=self.name,
            doi=doi,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            volume=volume,
            number=issue,
            pages=page,
            publisher=publisher,
            url=url,
            raw_response=msg,
        )

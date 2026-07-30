"""
DBLP Computer Science Bibliography API integration.
"""
from __future__ import annotations

import re
from typing import Optional
import aiohttp

from .base import MetadataSource, SourceRecord
from ..models.citation import Author
from ..utils.async_utils import fetch_json


class DBLPSource(MetadataSource):
    name = "DBLP"
    reliability_weight = 0.95  # High reliability for CS venues (ICML, NeurIPS, ICLR, etc.)

    SEARCH_URL = "https://dblp.org/search/publ/api"

    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        # DBLP query by DOI
        params = {"q": f"doi:{doi}", "format": "json", "h": 1}
        return await self._query(session, params)

    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        query = f"{title} {author_hint}".strip()
        params = {"q": query, "format": "json", "h": 1}
        return await self._query(session, params)

    async def _query(self, session: aiohttp.ClientSession, params: dict) -> Optional[SourceRecord]:
        resp = await fetch_json(session, self.SEARCH_URL, params=params)
        if not resp:
            return None
        hits = resp.get("result", {}).get("hits", {}).get("hit", [])
        if not hits:
            return None
        info = hits[0].get("info", {})
        return self._parse_info(info)

    def _parse_info(self, info: dict) -> SourceRecord:
        title = info.get("title", "").rstrip(".")

        # Authors
        authors: list[Author] = []
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        for a in authors_data:
            text = a.get("text", "") if isinstance(a, dict) else str(a)
            # Remove numerical suffixes like "0001"
            clean_text = re.sub(r"\s+\d{4}$", "", text)
            parts = clean_text.split()
            if len(parts) >= 2:
                authors.append(Author(given=" ".join(parts[:-1]), family=parts[-1], raw=clean_text))
            else:
                authors.append(Author(given="", family=clean_text, raw=clean_text))

        venue = info.get("venue", "")
        year = info.get("year")
        volume = info.get("volume")
        number = info.get("number")
        pages = info.get("pages")
        doi = info.get("doi")
        url = info.get("url")

        return SourceRecord(
            source_name=self.name,
            doi=doi,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            volume=volume,
            number=number,
            pages=pages,
            url=url,
            raw_response=info,
        )

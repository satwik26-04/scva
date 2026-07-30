"""
arXiv API integration.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional
import aiohttp

from .base import MetadataSource, SourceRecord
from ..models.citation import Author
from ..utils.async_utils import fetch_bytes


class ArXivSource(MetadataSource):
    name = "arXiv"
    reliability_weight = 0.80

    API_URL = "http://export.arxiv.org/api/query"

    async def fetch_by_doi(self, session: aiohttp.ClientSession, doi: str) -> Optional[SourceRecord]:
        return None  # arXiv API is queried via arXiv ID or title search

    async def fetch_by_arxiv_id(self, session: aiohttp.ClientSession, arxiv_id: str) -> Optional[SourceRecord]:
        clean_id = re.sub(r"^arxiv:", "", arxiv_id, flags=re.IGNORECASE).strip()
        params = f"id_list={clean_id}"
        url = f"{self.API_URL}?{params}"
        bytes_data = await fetch_bytes(session, url)
        if not bytes_data:
            return None
        return self._parse_xml(bytes_data)

    async def search_by_title(
        self, session: aiohttp.ClientSession, title: str, author_hint: str = ""
    ) -> Optional[SourceRecord]:
        clean_title = re.sub(r"[^\w\s]", "", title)
        url = f"{self.API_URL}?searchquery=ti:\"{clean_title}\"&max_results=1"
        bytes_data = await fetch_bytes(session, url)
        if not bytes_data:
            return None
        return self._parse_xml(bytes_data)

    def _parse_xml(self, xml_bytes: bytes) -> Optional[SourceRecord]:
        try:
            root = ET.fromstring(xml_bytes)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            entry = root.find("atom:entry", ns)
            if entry is None:
                return None

            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else ""

            authors: list[Author] = []
            for author_elem in entry.findall("atom:author", ns):
                name_elem = author_elem.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    name = name_elem.text.strip()
                    parts = name.split()
                    if len(parts) >= 2:
                        authors.append(Author(given=" ".join(parts[:-1]), family=parts[-1], raw=name))
                    else:
                        authors.append(Author(given="", family=name, raw=name))

            id_elem = entry.find("atom:id", ns)
            arxiv_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
            arxiv_id_match = re.search(r"abs/(\d{4}\.\d{4,5}(v\d+)?)", arxiv_url)
            arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else None

            published_elem = entry.find("atom:published", ns)
            year = published_elem.text[:4] if published_elem is not None and published_elem.text else None

            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""

            # Check for journal reference or DOI in arXiv metadata
            doi_elem = entry.find("arxiv:doi", ns)
            doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

            journal_ref_elem = entry.find("arxiv:journal_ref", ns)
            venue = journal_ref_elem.text.strip() if journal_ref_elem is not None and journal_ref_elem.text else "arXiv preprint"

            return SourceRecord(
                source_name=self.name,
                doi=doi,
                title=title,
                authors=authors,
                venue=venue,
                year=year,
                url=arxiv_url,
                arxiv_id=arxiv_id,
                abstract=abstract,
            )
        except Exception:
            return None

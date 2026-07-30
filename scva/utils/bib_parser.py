"""
BibTeX parser wrapper supporting both bibtexparser v1 and v2.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import bibtexparser

from ..models.citation import Author, BibEntry


def parse_bib_file(bib_path: str | Path) -> list[BibEntry]:
    """Parse a .bib file and return a list of BibEntry objects."""
    bib_path = Path(bib_path)
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    return parse_bib_string(text)


def parse_bib_string(text: str) -> list[BibEntry]:
    """Parse a BibTeX string and return BibEntry objects."""
    try:
        # Try bibtexparser v1 first (most common)
        bib_database = bibtexparser.loads(text)
        entries: list[BibEntry] = []
        for entry in bib_database.entries:
            entries.append(_convert_v1_entry(entry))
        return entries
    except AttributeError:
        # Fallback to bibtexparser v2
        library = bibtexparser.parse_string(text)
        entries: list[BibEntry] = []
        for entry in library.entries:
            entries.append(_convert_v2_entry(entry))
        return entries


def _convert_v1_entry(fields: dict) -> BibEntry:
    key = fields.get("ID", fields.get("id", "unknown"))
    entry_type = fields.get("ENTRYTYPE", fields.get("entrytype", "article")).lower()

    authors = _parse_authors(fields.get("author", ""))
    doi = _clean_doi(fields.get("doi", ""))
    arxiv_id = _extract_arxiv_id(
        fields.get("eprint", "")
        or fields.get("journal", "")
        or fields.get("url", "")
    )

    venue = (
        fields.get("journal")
        or fields.get("booktitle")
        or fields.get("series")
        or ""
    )

    return BibEntry(
        key=key,
        entry_type=entry_type,
        title=_strip_braces(fields.get("title", "")),
        authors=authors,
        year=fields.get("year"),
        venue=_strip_braces(venue),
        volume=fields.get("volume"),
        number=fields.get("number"),
        pages=fields.get("pages"),
        doi=doi,
        url=fields.get("url"),
        publisher=fields.get("publisher"),
        arxiv_id=arxiv_id,
        pmid=fields.get("pmid"),
        isbn=fields.get("isbn"),
        edition=fields.get("edition"),
        note=fields.get("note"),
        raw_fields=fields,
    )


def _convert_v2_entry(entry: Any) -> BibEntry:
    fields = {f.key: f.value for f in entry.fields}
    fields["ID"] = entry.key
    fields["ENTRYTYPE"] = entry.type
    return _convert_v1_entry(fields)


def _parse_authors(author_str: str) -> list[Author]:
    if not author_str.strip():
        return []
    parts = re.split(r"\s+and\s+", author_str.strip(), flags=re.IGNORECASE)
    authors = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        authors.append(_parse_single_author(part))
    return authors


def _parse_single_author(raw: str) -> Author:
    raw_stripped = _strip_braces(raw).strip()
    if "," in raw_stripped:
        family, _, given = raw_stripped.partition(",")
        return Author(given=given.strip(), family=family.strip(), raw=raw_stripped)
    parts = raw_stripped.split()
    if len(parts) >= 2:
        return Author(given=" ".join(parts[:-1]), family=parts[-1], raw=raw_stripped)
    return Author(given="", family=raw_stripped, raw=raw_stripped)


def _strip_braces(s: str) -> str:
    return re.sub(r"[{}]", "", s)


def _clean_doi(doi: str) -> Optional[str]:
    if not doi:
        return None
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi if doi else None


def _extract_arxiv_id(s: str) -> Optional[str]:
    if not s:
        return None
    m = re.search(r"(\d{4}\.\d{4,5})", s)
    if m:
        return m.group(1)
    m = re.search(r"arxiv[:/]([^\s,}]+)", s, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def bib_entry_to_string(entry: BibEntry) -> str:
    lines = [f"@{entry.entry_type}{{{entry.key},"]

    def _field(name: str, val: Optional[str]) -> None:
        if val:
            lines.append(f"  {name}={{{val}}},")

    _field("title", entry.title)
    if entry.authors:
        author_str = " and ".join(
            f"{a.family}, {a.given}" if a.family and a.given else a.full_name()
            for a in entry.authors
        )
        lines.append(f"  author={{{author_str}}},")
    _field("journal" if entry.entry_type == "article" else "booktitle", entry.venue)
    _field("year", entry.year)
    _field("volume", entry.volume)
    _field("number", entry.number)
    _field("pages", entry.pages)
    _field("doi", entry.doi)
    _field("url", entry.url)
    _field("publisher", entry.publisher)
    _field("arxiv_id", entry.arxiv_id)

    lines.append("}")
    return "\n".join(lines)

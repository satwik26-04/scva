"""
Stage 2 & 3: Metadata Verification & Multi-Source Validation across Crossref, DBLP, OpenAlex, etc.
"""
from __future__ import annotations

import asyncio
import aiohttp
from typing import Optional

from ..models.citation import BibEntry
from ..models.report import MetadataVerification
from ..cache.manager import CacheManager
from ..sources.base import SourceRecord
from ..sources.crossref import CrossrefSource
from ..sources.dblp import DBLPSource
from ..sources.openalex import OpenAlexSource
from ..sources.semantic_scholar import SemanticScholarSource
from ..sources.arxiv_source import ArXivSource
from ..sources.consensus import ConsensusEngine


async def run_stage_02_03(
    entries: list[BibEntry],
    cache: CacheManager,
    sources: Optional[list] = None,
) -> tuple[dict[str, MetadataVerification], dict[str, BibEntry]]:
    """
    Fetch metadata concurrently for all entries, apply consensus,
    and return (verifications_map, corrected_entries_map).
    """
    if sources is None:
        sources = [
            CrossrefSource(),
            DBLPSource(),
            OpenAlexSource(),
            SemanticScholarSource(),
            ArXivSource(),
        ]

    consensus = ConsensusEngine()
    verifications: dict[str, MetadataVerification] = {}
    corrected_entries: dict[str, BibEntry] = {}

    async with aiohttp.ClientSession() as session:
        tasks = [
            _process_entry(entry, session, sources, cache, consensus)
            for entry in entries
        ]
        results = await asyncio.gather(*tasks)

        for key, meta, corr in results:
            verifications[key] = meta
            corrected_entries[key] = corr

    return verifications, corrected_entries


async def _process_entry(
    entry: BibEntry,
    session: aiohttp.ClientSession,
    sources: list,
    cache: CacheManager,
    consensus: ConsensusEngine,
) -> tuple[str, MetadataVerification, BibEntry]:
    records: list[SourceRecord] = []

    # 1. Fetch by DOI if present
    if entry.doi:
        cached_doi = cache.get_metadata("doi", entry.doi)
        if cached_doi:
            # Parse cached JSON if available
            pass

        for source in sources:
            try:
                rec = await source.fetch_by_doi(session, entry.doi)
                if rec:
                    records.append(rec)
            except Exception:
                pass

    # 2. If no DOI or no records returned, search by title with strict match check
    if not records and entry.title:
        author_hint = entry.authors[0].family if entry.authors else ""
        for source in sources:
            try:
                rec = await source.search_by_title(session, entry.title, author_hint)
                if rec and rec.title:
                    # Enforce strict title similarity check (>= 0.85)
                    from ..utils.text_utils import title_similarity
                    if title_similarity(entry.title, rec.title) >= 0.85:
                        records.append(rec)
                        break  # Stop after first strong match
            except Exception:
                pass

    # 3. If arXiv ID present, fetch from arXiv source
    if entry.arxiv_id:
        arxiv_src = ArXivSource()
        try:
            rec = await arxiv_src.fetch_by_arxiv_id(session, entry.arxiv_id)
            if rec:
                records.append(rec)
        except Exception:
            pass

    meta, corrected = consensus.merge_and_verify(entry, records)
    return entry.key, meta, corrected

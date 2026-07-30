"""
Stage 4 & 5: Paper Retrieval & Semantic Understanding.
Retrieves abstract / PDF text and builds structured PaperKnowledge object.
"""
from __future__ import annotations

import asyncio
import aiohttp
from typing import Optional

from ..models.citation import BibEntry
from ..models.paper import PaperKnowledge
from ..cache.manager import CacheManager
from ..sources.openalex import OpenAlexSource
from ..sources.semantic_scholar import SemanticScholarSource
from ..sources.arxiv_source import ArXivSource
from ..utils.async_utils import fetch_bytes
from ..utils.pdf_utils import extract_text_from_pdf_bytes


async def run_stage_04_05(
    entries: list[BibEntry],
    cache: CacheManager,
) -> dict[str, PaperKnowledge]:
    """Retrieve abstract/PDF text for all entries and extract structured knowledge."""
    knowledge_map: dict[str, PaperKnowledge] = {}

    async with aiohttp.ClientSession() as session:
        tasks = [_retrieve_paper(entry, session, cache) for entry in entries]
        results = await asyncio.gather(*tasks)
        for key, pk in results:
            knowledge_map[key] = pk

    return knowledge_map


async def _retrieve_paper(
    entry: BibEntry,
    session: aiohttp.ClientSession,
    cache: CacheManager,
) -> tuple[str, PaperKnowledge]:
    abstract = ""
    pdf_text = ""

    # Check cache first
    cache_key = entry.doi or entry.arxiv_id or entry.key
    cached_pdf = cache.get_pdf_text(cache_key)
    if cached_pdf:
        pdf_text = cached_pdf

    # Fetch abstract via Semantic Scholar or OpenAlex if not cached
    if not pdf_text:
        ss = SemanticScholarSource()
        rec = None
        if entry.doi:
            rec = await ss.fetch_by_doi(session, entry.doi)
        elif entry.title:
            rec = await ss.search_by_title(session, entry.title)

        if rec and rec.abstract:
            abstract = rec.abstract

        if not abstract:
            oa = OpenAlexSource()
            if entry.doi:
                rec_oa = await oa.fetch_by_doi(session, entry.doi)
            elif entry.title:
                rec_oa = await oa.search_by_title(session, entry.title)

            if rec_oa and rec_oa.abstract:
                abstract = rec_oa.abstract

    # Try downloading arXiv PDF if available
    if entry.arxiv_id and not pdf_text:
        pdf_url = f"https://arxiv.org/pdf/{entry.arxiv_id}.pdf"
        pdf_bytes = await fetch_bytes(session, pdf_url)
        if pdf_bytes:
            pdf_text = extract_text_from_pdf_bytes(pdf_bytes, max_pages=15)
            if pdf_text:
                cache.set_pdf_text(cache_key, pdf_text)

    # Extract basic sections from text
    full_text = pdf_text or abstract
    problem, method, conclusions = _heuristic_extract(full_text)

    pk = PaperKnowledge(
        key=entry.key,
        title=entry.title,
        abstract=abstract,
        problem=problem,
        method=method,
        conclusions=conclusions,
        pdf_available=bool(pdf_text),
        abstract_only=bool(abstract and not pdf_text),
    )

    return entry.key, pk


def _heuristic_extract(text: str) -> tuple[str, str, str]:
    """Basic sentence-level heuristic extraction of problem, method, conclusion."""
    if not text:
        return "", "", ""

    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
    problem = ""
    method = ""
    conclusion = ""

    for s in sentences:
        s_lower = s.lower()
        if not problem and any(w in s_lower for w in ("challenge", "problem", "aims to", "we study", "address")):
            problem = s
        elif not method and any(w in s_lower for w in ("propose", "introduce", "framework", "method", "architecture", "model")):
            method = s
        elif not conclusion and any(w in s_lower for w in ("demonstrate", "show", "achieve", "outperform", "result", "conclude")):
            conclusion = s

    return problem, method, conclusion

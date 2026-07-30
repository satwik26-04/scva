"""
Stage 12: Duplicate Detection.
Detects duplicate BibTeX keys, duplicate DOIs, and near-identical titles.
"""
from __future__ import annotations

from ..models.citation import BibEntry
from ..models.report import DuplicateInfo
from ..utils.text_utils import title_similarity


def run_stage_12(entries: list[BibEntry]) -> dict[str, DuplicateInfo]:
    """Identify duplicate BibTeX entries by DOI or Title similarity."""
    duplicates: dict[str, DuplicateInfo] = {}

    doi_map: dict[str, str] = {}
    title_map: dict[str, str] = {}

    for entry in entries:
        # 1. DOI duplicate check
        if entry.doi:
            clean_doi = entry.doi.lower().strip()
            if clean_doi in doi_map:
                existing_key = doi_map[clean_doi]
                duplicates[entry.key] = DuplicateInfo(
                    duplicate_of=existing_key,
                    reason=f"Duplicate DOI ({entry.doi}) shared with key '{existing_key}'.",
                )
                continue
            else:
                doi_map[clean_doi] = entry.key

        # 2. Title similarity check
        if entry.title:
            is_dup = False
            for existing_title, existing_key in title_map.items():
                if title_similarity(entry.title, existing_title) > 0.92:
                    duplicates[entry.key] = DuplicateInfo(
                        duplicate_of=existing_key,
                        reason=f"Near-identical title matched with key '{existing_key}'.",
                    )
                    is_dup = True
                    break

            if not is_dup:
                title_map[entry.title] = entry.key

    return duplicates

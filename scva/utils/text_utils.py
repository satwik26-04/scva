"""
Text normalization, string similarity, and matching utilities.
"""
from __future__ import annotations

import re
import unicodedata
from rapidfuzz import fuzz


def normalize_title(title: str) -> str:
    """Normalize title string for robust fuzzy matching."""
    if not title:
        return ""
    # Lowercase & NFD unicode normalization
    text = title.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Strip LaTeX commands & braces
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_similarity(t1: str, t2: str) -> float:
    """Return normalized similarity ratio (0.0 to 1.0) between two paper titles."""
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return 0.0
    return fuzz.token_sort_ratio(n1, n2) / 100.0


def normalize_author_name(name: str) -> str:
    """Normalize author name (e.g. 'Yann LeCun' -> 'yann lecun')."""
    if not name:
        return ""
    text = name.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def author_list_match(list1: list[str], list2: list[str]) -> float:
    """Compare two author lists and return a match score (0.0 to 1.0)."""
    if not list1 or not list2:
        return 0.0

    norm1 = [normalize_author_name(a) for a in list1]
    norm2 = [normalize_author_name(a) for a in list2]

    # Compare surnames / full names
    matches = 0
    for a1 in norm1:
        for a2 in norm2:
            # Check family name or high fuzzy match
            if a1 in a2 or a2 in a1 or fuzz.ratio(a1, a2) > 85:
                matches += 1
                break

    return matches / max(len(norm1), len(norm2))


def extract_doi_from_text(text: str) -> str | None:
    """Extract standard DOI string from raw text/URL."""
    if not text:
        return None
    match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", text)
    if match:
        doi = match.group(0).rstrip(".,;")
        return doi
    return None

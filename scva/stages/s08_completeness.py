"""
Stage 8: Citation Completeness.
Detects important scientific claims that lack citations.
"""
from __future__ import annotations

import re
from ..models.citation import CitationGraph


UNSUPPORTED_PATTERNS = [
    r"it has been (shown|proven|demonstrated|observed)\b(?!.*\\cite)",
    r"studies have (shown|demonstrated|found)\b(?!.*\\cite)",
    r"recent work (suggests|indicates|shows)\b(?!.*\\cite)",
    r"prior (research|work) (has|demonstrates)\b(?!.*\\cite)",
    r"state-of-the-art results?\b(?!.*\\cite)",
]


def run_stage_08(tex_text: str) -> list[dict[str, str]]:
    """Scan manuscript LaTeX text for unsupported claims lacking citations."""
    missing_citations = []

    lines = tex_text.splitlines()
    for idx, line in enumerate(lines, 1):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("%"):
            continue

        for pat in UNSUPPORTED_PATTERNS:
            if re.search(pat, clean_line, re.IGNORECASE) and "\\cite" not in clean_line:
                missing_citations.append({
                    "line": str(idx),
                    "text": clean_line,
                    "reason": "Assertive claim statement made without an attached citation.",
                })
                break

    return missing_citations

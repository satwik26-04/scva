"""
Stage 1: Parse Inputs — Construct CitationGraph from .bib and .tex inputs.
"""
from __future__ import annotations

from pathlib import Path
from ..models.citation import CitationGraph
from ..utils.bib_parser import parse_bib_file
from ..utils.tex_parser import parse_tex_file


def run_stage_01(bib_path: str | Path, tex_path: str | Path) -> CitationGraph:
    """Parse .bib and .tex files and construct full CitationGraph."""
    entries = parse_bib_file(bib_path)
    entries_map = {e.key: e for e in entries}

    occurrences = parse_tex_file(tex_path)
    occurrences_map: dict[str, list] = {}
    for occ in occurrences:
        occurrences_map.setdefault(occ.key, []).append(occ)

    return CitationGraph(entries=entries_map, occurrences=occurrences_map)

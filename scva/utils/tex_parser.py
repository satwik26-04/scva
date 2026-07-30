"""
LaTeX manuscript parser for extracting citation occurrences, sections, and claim contexts.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..models.citation import CitationOccurrence


def parse_tex_file(tex_path: str | Path) -> list[CitationOccurrence]:
    """Parse a .tex file and extract all citation occurrences with surrounding context."""
    tex_path = Path(tex_path)
    text = tex_path.read_text(encoding="utf-8", errors="replace")
    return parse_tex_string(text, str(tex_path))


def parse_tex_string(text: str, file_path: str = "manuscript.tex") -> list[CitationOccurrence]:
    """Extract citation occurrences from LaTeX text."""
    # Remove LaTeX comments
    text_clean = re.sub(r"(?<!\\)%.*", "", text)

    lines = text_clean.splitlines()
    occurrences: list[CitationOccurrence] = []

    current_section = "Introduction"
    current_subsection = ""

    # Regex for section headings
    sec_pattern = re.compile(r"\\section\*?\{([^}]+)\}")
    subsec_pattern = re.compile(r"\\subsection\*?\{([^}]+)\}")

    # Regex for citations: \cite, \citep, \citet, \citeauthor, \citeyear, etc.
    cite_pattern = re.compile(r"\\cite[a-zA-Z]*\{([^}]+)\}")

    for idx, line in enumerate(lines, 1):
        # Track section context
        sec_match = sec_pattern.search(line)
        if sec_match:
            current_section = _strip_latex(sec_match.group(1))
            current_subsection = ""
            continue

        subsec_match = subsec_pattern.search(line)
        if subsec_match:
            current_subsection = _strip_latex(subsec_match.group(1))
            continue

        # Check for citations
        for cite_match in cite_pattern.finditer(line):
            raw_keys = cite_match.group(1)
            # Handle multiple keys like \cite{key1, key2}
            keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

            # Extract sentence context
            sentence = _extract_sentence(lines, idx - 1, cite_match.start())
            paragraph = _extract_paragraph(lines, idx - 1)
            claim = _extract_claim_fragment(sentence)

            for key in keys:
                occurrences.append(
                    CitationOccurrence(
                        key=key,
                        tex_file=file_path,
                        line_number=idx,
                        section=current_section,
                        subsection=current_subsection,
                        sentence=_strip_latex(sentence),
                        paragraph=_strip_latex(paragraph),
                        nearby_claim=_strip_latex(claim),
                    )
                )

    return occurrences


def _extract_sentence(lines: list[str], line_idx: int, char_pos: int) -> str:
    """Extract full sentence containing line_idx."""
    # Grab surrounding context (-2 to +2 lines)
    start = max(0, line_idx - 2)
    end = min(len(lines), line_idx + 3)
    block = " ".join(lines[start:end])

    # Basic sentence splitter
    sentences = re.split(r"(?<=[.!?])\s+", block)
    target_line = lines[line_idx]

    for s in sentences:
        # Find sentence containing the target line snippet
        if target_line[:20].strip() in s or "\\cite" in s:
            return s.strip()

    return target_line.strip()


def _extract_paragraph(lines: list[str], line_idx: int) -> str:
    """Extract paragraph surrounding line_idx (demarcated by empty lines)."""
    start = line_idx
    while start > 0 and lines[start - 1].strip() != "":
        start -= 1

    end = line_idx
    while end < len(lines) - 1 and lines[end + 1].strip() != "":
        end += 1

    return " ".join(lines[start : end + 1]).strip()


def _extract_claim_fragment(sentence: str) -> str:
    """Extract the main statement/claim portion from a sentence containing a citation."""
    # Remove the citation command itself
    cleaned = re.sub(r"\\cite[a-zA-Z]*\{[^}]+\}", "", sentence)
    # Remove excess whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _strip_latex(text: str) -> str:
    """Strip basic LaTeX formatting commands for clean plain text."""
    text = re.sub(r"\\[a-zA-Z]+\*?(\{([^}]+)\})?", r"\2", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

"""
PDF extraction and reading utilities using pypdf.
"""
from __future__ import annotations

import io
from pathlib import Path
import pypdf


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 20) -> str:
    """Extract plain text from raw PDF bytes."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for idx, page in enumerate(reader.pages):
            if idx >= max_pages:
                break
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)
    except Exception as e:
        return ""


def extract_text_from_pdf_file(pdf_path: str | Path, max_pages: int = 20) -> str:
    """Extract plain text from local PDF file."""
    path = Path(pdf_path)
    if not path.exists():
        return ""
    try:
        bytes_content = path.read_bytes()
        return extract_text_from_pdf_bytes(bytes_content, max_pages=max_pages)
    except Exception:
        return ""

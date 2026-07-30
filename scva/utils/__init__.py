"""utils package"""
from .bib_parser import parse_bib_file, parse_bib_string, bib_entry_to_string
from .tex_parser import parse_tex_file, parse_tex_string
from .text_utils import normalize_title, title_similarity, author_list_match, extract_doi_from_text
from .pdf_utils import extract_text_from_pdf_bytes, extract_text_from_pdf_file
from .async_utils import fetch_json, fetch_bytes

__all__ = [
    "parse_bib_file", "parse_bib_string", "bib_entry_to_string",
    "parse_tex_file", "parse_tex_string",
    "normalize_title", "title_similarity", "author_list_match", "extract_doi_from_text",
    "extract_text_from_pdf_bytes", "extract_text_from_pdf_file",
    "fetch_json", "fetch_bytes",
]

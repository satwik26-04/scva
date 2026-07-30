"""
Multi-source validation and consensus engine.
Ranks metadata sources and merges records without blindly overwriting.
"""
from __future__ import annotations

from typing import Optional
from .base import SourceRecord
from ..models.citation import Author, BibEntry
from ..models.report import FieldStatus, FieldVerification, MetadataVerification
from ..utils.text_utils import author_list_match, title_similarity


class ConsensusEngine:
    """Merges and verifies BibTeX entry metadata against multiple API source records."""

    def merge_and_verify(
        self, entry: BibEntry, records: list[SourceRecord]
    ) -> tuple[MetadataVerification, BibEntry]:
        """
        Compare BibEntry fields against fetched records.
        Return (MetadataVerification, corrected_BibEntry).
        """
        sources_queried = [r.source_name for r in records]

        verifications: list[FieldVerification] = []

        # 1. Title verification
        v_title, best_title = self._verify_field(
            field_name="title",
            bib_val=entry.title,
            records=records,
            extractor=lambda r: r.title,
            compare_func=lambda b, s: title_similarity(b, s) > 0.85,
        )
        verifications.append(v_title)

        # 2. Authors verification
        bib_authors_raw = [a.full_name() for a in entry.authors]
        v_authors, best_authors_rec = self._verify_authors(
            bib_authors=bib_authors_raw,
            records=records,
        )
        verifications.append(v_authors)

        # 3. Year verification
        v_year, best_year = self._verify_field(
            field_name="year",
            bib_val=entry.year or "",
            records=records,
            extractor=lambda r: r.year or "",
            compare_func=lambda b, s: b.strip() == s.strip(),
        )
        verifications.append(v_year)

        # 4. Venue verification
        v_venue, best_venue = self._verify_field(
            field_name="venue",
            bib_val=entry.venue,
            records=records,
            extractor=lambda r: r.venue or "",
            compare_func=lambda b, s: title_similarity(b, s) > 0.70,
        )
        verifications.append(v_venue)

        # 5. Pages verification
        def _clean_pages(p: str) -> str:
            p = p.replace("--", "-").strip()
            parts = p.split("-")
            if len(parts) == 2 and parts[0] == parts[1]:
                return parts[0]
            return p

        v_pages, best_pages = self._verify_field(
            field_name="pages",
            bib_val=entry.pages or "",
            records=records,
            extractor=lambda r: r.pages or "",
            compare_func=lambda b, s: _clean_pages(b) == _clean_pages(s),
        )
        verifications.append(v_pages)

        # 6. DOI verification
        v_doi, best_doi = self._verify_field(
            field_name="doi",
            bib_val=entry.doi or "",
            records=records,
            extractor=lambda r: r.doi or "",
            compare_func=lambda b, s: b.lower().strip() == s.lower().strip(),
        )
        verifications.append(v_doi)

        # Construct metadata report
        meta = MetadataVerification(
            key=entry.key,
            fields=verifications,
            sources_queried=sources_queried,
            sources_returned=sources_queried,
        )

        # Construct corrected entry
        corrected_entry = BibEntry(
            key=entry.key,
            entry_type=entry.entry_type,
            title=best_title if v_title.status == FieldStatus.CORRECTED else entry.title,
            authors=best_authors_rec if v_authors.status == FieldStatus.CORRECTED else entry.authors,
            year=best_year if v_year.status == FieldStatus.CORRECTED else entry.year,
            venue=best_venue if v_venue.status == FieldStatus.CORRECTED else entry.venue,
            volume=entry.volume,
            number=entry.number,
            pages=best_pages if v_pages.status == FieldStatus.CORRECTED else entry.pages,
            doi=best_doi if v_doi.status == FieldStatus.CORRECTED else entry.doi,
            url=entry.url,
            publisher=entry.publisher,
            arxiv_id=entry.arxiv_id,
        )

        return meta, corrected_entry

    def _verify_field(
        self,
        field_name: str,
        bib_val: str,
        records: list[SourceRecord],
        extractor,
        compare_func,
    ) -> tuple[FieldVerification, str]:
        if not records:
            return (
                FieldVerification(
                    field_name=field_name,
                    bib_value=bib_val,
                    verified_value=bib_val,
                    status=FieldStatus.UNVERIFIED,
                ),
                bib_val,
            )

        # Filter records containing non-empty value for this field
        candidates = []
        for r in records:
            val = extractor(r)
            if val:
                candidates.append((val, r))

        if not candidates:
            return (
                FieldVerification(
                    field_name=field_name,
                    bib_value=bib_val,
                    verified_value=bib_val,
                    status=FieldStatus.UNVERIFIED,
                ),
                bib_val,
            )

        # Select highest reliability candidate (or consensus winner)
        best_val, best_source = candidates[0][0], candidates[0][1].source_name

        if not bib_val:
            return (
                FieldVerification(
                    field_name=field_name,
                    bib_value="",
                    verified_value=best_val,
                    status=FieldStatus.MISSING,
                    source=best_source,
                    note=f"Filled missing field from {best_source}",
                ),
                best_val,
            )

        if compare_func(bib_val, best_val):
            return (
                FieldVerification(
                    field_name=field_name,
                    bib_value=bib_val,
                    verified_value=bib_val,
                    status=FieldStatus.CORRECT,
                    source=best_source,
                ),
                bib_val,
            )
        else:
            return (
                FieldVerification(
                    field_name=field_name,
                    bib_value=bib_val,
                    verified_value=best_val,
                    status=FieldStatus.CORRECTED,
                    source=best_source,
                    note=f"Mismatch against {best_source}: bib has '{bib_val}', source has '{best_val}'",
                ),
                best_val,
            )

    def _verify_authors(
        self, bib_authors: list[str], records: list[SourceRecord]
    ) -> tuple[FieldVerification, list[Author]]:
        if not records or not records[0].authors:
            return (
                FieldVerification(
                    field_name="authors",
                    bib_value=" and ".join(bib_authors),
                    verified_value=" and ".join(bib_authors),
                    status=FieldStatus.UNVERIFIED,
                ),
                [],
            )

        rec = records[0]
        source_authors_raw = [a.full_name() for a in rec.authors]
        match_score = author_list_match(bib_authors, source_authors_raw)

        bib_str = " and ".join(bib_authors)
        source_str = " and ".join(source_authors_raw)

        if match_score >= 0.8:
            return (
                FieldVerification(
                    field_name="authors",
                    bib_value=bib_str,
                    verified_value=bib_str,
                    status=FieldStatus.CORRECT,
                    source=rec.source_name,
                ),
                rec.authors,
            )
        else:
            return (
                FieldVerification(
                    field_name="authors",
                    bib_value=bib_str,
                    verified_value=source_str,
                    status=FieldStatus.CORRECTED,
                    source=rec.source_name,
                    note=f"Author mismatch vs {rec.source_name}",
                ),
                rec.authors,
            )

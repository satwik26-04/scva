"""
Stage 11: Version Checking.
Detects arXiv preprint entries that have since been published in peer-reviewed venues.
"""
from __future__ import annotations

from ..models.citation import BibEntry
from ..models.report import MetadataVerification, VersionInfo


def run_stage_11(
    entries: list[BibEntry],
    verifications: dict[str, MetadataVerification],
) -> dict[str, VersionInfo]:
    """Check if any arXiv entries have published venue updates available."""
    version_map: dict[str, VersionInfo] = {}

    for entry in entries:
        is_arxiv = entry.is_arxiv_only()
        meta = verifications.get(entry.key)

        if is_arxiv and meta:
            # Check if verified venue is a peer-reviewed conference/journal
            venue_field = next((f for f in meta.fields if f.field_name == "venue"), None)
            if venue_field and venue_field.verified_value and "arxiv" not in venue_field.verified_value.lower():
                version_map[entry.key] = VersionInfo(
                    key=entry.key,
                    current_version="arxiv",
                    recommended_version="conference/journal",
                    note=f"Paper published in '{venue_field.verified_value}'. Update BibTeX entry from arXiv to camera-ready venue.",
                )
            else:
                version_map[entry.key] = VersionInfo(
                    key=entry.key,
                    current_version="arxiv",
                    recommended_version="arxiv",
                    note="Preprint version; no published venue detected.",
                )
        else:
            version_map[entry.key] = VersionInfo(
                key=entry.key,
                current_version="published",
                recommended_version="published",
                note="Published peer-reviewed entry.",
            )

    return version_map

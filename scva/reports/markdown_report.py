"""
Markdown Report Exporter for SCVA.
"""
from __future__ import annotations

from pathlib import Path
from ..models.report import FinalReport


def generate_markdown_report(report: FinalReport, output_path: Path) -> Path:
    """Generate Markdown report artifact."""
    lines = []
    integ = report.integrity

    lines.append("# Scientific Citation Verification Report (SCVA)\n")
    lines.append(f"**Run ID:** `{report.run_id}` | **SCVA Version:** `{report.scva_version}`\n")
    lines.append(f"**Manuscript:** `{report.input_tex}`\n")
    lines.append(f"**Bibliography:** `{report.input_bib}`\n")
    lines.append("---\n")

    # Quality Scores Summary
    lines.append("## Overall Audit Summary & Scores\n")
    lines.append(f"- **Publication Readiness Score:** `{integ.publication_readiness_score * 100:.1f}%`")
    lines.append(f"- **Bibliography Quality Score:** `{integ.bibliography_quality_score * 100:.1f}%`")
    lines.append(f"- **Citation Quality Score:** `{integ.citation_quality_score * 100:.1f}%`")
    lines.append(f"- **Total References:** {integ.total_references}")
    lines.append(f"- **Verified References:** {integ.verified_count}")
    lines.append(f"- **Corrected Entries:** {integ.corrected_count}")
    lines.append(f"- **Metadata Mismatches:** {integ.metadata_error_count} (Years: {integ.wrong_year}, Pages: {integ.wrong_pages}, Venues: {integ.wrong_venue}, Authors: {integ.wrong_authors})")
    lines.append(f"- **Unsupported / Contradicted Claims:** {integ.unsupported_claims + integ.contradicted_claims}")
    lines.append(f"- **Duplicate References:** {integ.duplicate_references}")
    lines.append(f"- **Uncited BibTeX Entries:** {integ.unused_references}\n")

    # Pending AI Queries notice if any
    if report.ai_queries_pending > 0:
        lines.append("> [!IMPORTANT]")
        lines.append(f"> **{report.ai_queries_pending} queries pending AI Oracle review.**")
        lines.append("> Run `scva ask` to inspect pending queries or delegate to your AI assistant.\n")

    # Detailed Per-Entry Verification Results
    lines.append("## Per-Citation Verification Audit\n")

    for entry in report.entries:
        status_tag = f"[{entry.overall_status()}]"
        lines.append(f"### {status_tag} `{entry.key}` — Confidence: {entry.confidence.label()} ({entry.confidence.overall * 100:.0f}%)\n")
        lines.append(f"- **Title:** {entry.title}")
        lines.append(f"- **Authors:** {', '.join(entry.authors)}")
        lines.append(f"- **Venue/Year:** {entry.venue} ({entry.year})\n")

        lines.append("| Field | Verified Value | Status | Source |")
        lines.append("|---|---|---|---|")
        for f in entry.fields:
            s_tag = f"[{f.status}]"
            lines.append(f"| `{f.field}` | `{f.value}` | {s_tag} | {f.source} |")
        lines.append("")

        if entry.claim_supports:
            lines.append("**Claim Support Statements:**")
            for cs in entry.claim_supports:
                c_tag = f"[{cs.label}]"
                lines.append(f"- {c_tag} Claim: *\"{cs.claim_text}\"*")
                if cs.evidence_quote:
                    lines.append(f"  > *\"{cs.evidence_quote}\"* ({cs.evidence_location})")
            lines.append("")

        # Recommendations
        if entry.recommendations:
            lines.append("**Recommendations:**")
            for rec in entry.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        lines.append("---\n")

    output_path = Path(output_path)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path

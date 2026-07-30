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
        status_icon = "✅" if entry.overall_status() == "OK" else "⚠️"
        lines.append(f"### {status_icon} `{entry.key}` — Confidence: {entry.confidence.label()} ({entry.confidence.overall * 100:.0f}%)\n")

        # Metadata table
        lines.append("| Field | Current BibTeX Value | Verified Value | Status | Source |")
        lines.append("|---|---|---|---|---|")
        for f in entry.metadata.fields:
            s_icon = "✅" if f.status == "CORRECT" else ("🔧" if f.status == "CORRECTED" else "❓")
            lines.append(f"| `{f.field_name}` | {f.bib_value} | {f.verified_value} | {s_icon} {f.status} | {f.source} |")
        lines.append("")

        # Claims Supported
        if entry.claim_supports:
            lines.append("**Claim Support Analysis:**")
            for cs in entry.claim_supports:
                c_icon = "✅" if cs.label in ("FULLY_SUPPORTED", "PARTIALLY_SUPPORTED") else "❌"
                lines.append(f"- {c_icon} **[{cs.label}]** {cs.explanation}")
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

"""
CSV Exporter for SCVA.
"""
from __future__ import annotations

import csv
from pathlib import Path
from ..models.report import FinalReport


def generate_csv_export(report: FinalReport, output_path: Path) -> Path:
    """Generate spreadsheet-friendly CSV summary."""
    output_path = Path(output_path)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Citation Key",
            "Overall Status",
            "Confidence Level",
            "Confidence Score",
            "Metadata Errors",
            "Claim Status",
            "Is Duplicate",
            "Recommendations",
        ])

        for entry in report.entries:
            err_count = len(entry.metadata.errors())
            claim_status = entry.claim_supports[0].label.value if entry.claim_supports else "UNVERIFIED"
            recs = " | ".join(entry.recommendations)

            writer.writerow([
                entry.key,
                entry.overall_status(),
                entry.confidence.label(),
                f"{entry.confidence.overall:.2f}",
                err_count,
                claim_status,
                entry.is_duplicate,
                recs,
            ])

    return output_path

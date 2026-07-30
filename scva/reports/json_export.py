"""
JSON Exporter for SCVA.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from ..models.report import FinalReport


def generate_json_export(report: FinalReport, output_path: Path) -> Path:
    """Generate machine-readable JSON export."""
    data = asdict(report)
    output_path = Path(output_path)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return output_path

"""
HTML Dashboard Exporter for SCVA.
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from ..models.report import FinalReport


def generate_html_report(report: FinalReport, output_path: Path) -> Path:
    """Generate HTML dashboard report artifact using Jinja2."""
    template_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("report.html")

    rendered = template.render(report=report)
    output_path = Path(output_path)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path

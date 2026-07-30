"""
Command Line Interface (CLI) for SCVA built with Click and Rich.
Features a stunning, color-coded terminal dashboard UI.
"""
from __future__ import annotations

import os
import sys
import asyncio
import json
from pathlib import Path
import click
from .config import ConfigManager
from .pipeline import VerificationPipeline
from .oracle import FileBasedOracle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Force UTF-8 encoding for Windows terminal output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console(force_terminal=True, record=True)


HEADER_BANNER = """
 ███████╗██╗   ██╗██████╗ ██████╗ 
 ██╔════╝██║   ██║██╔══██╗██╔══██╗
 ███████╗██║   ██║██████╔╝███████║
 ╚════██║██║   ██║██╔═══╝ ██╔══██║
 ███████║╚██████╔╝██║     ██║  ██║
 ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝
 Scientific Citation Verification Agent v1.0.0
"""


@click.group()
def main():
    """Scientific Citation Verification Agent (SCVA) — Production-grade citation audit tool."""
    pass


# ---------------------------------------------------------------------------
# AUDIT COMMAND
# ---------------------------------------------------------------------------

@main.command()
@click.argument("bib_path", type=click.Path(exists=True))
@click.argument("tex_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./scva_output", help="Directory to save audit artifacts.")
@click.option(
    "--oracle-mode",
    "-m",
    default=None,
    help="AI Oracle provider mode: antigravity, gemini, openai, claude, deepseek, moonshot, ollama, openrouter, nanogpt, glm, null.",
)
@click.option("--model", default=None, help="LLM model override (e.g. gpt-4o-mini, llama3.2, claude-3-5-haiku).")
def audit(bib_path: str, tex_path: str, output_dir: str, oracle_mode: str | None, model: str | None):
    """Run full 18-stage citation verification audit on a manuscript and bibliography."""
    cfg = ConfigManager()
    mode = oracle_mode or cfg.get_default_oracle()

    console.print(Panel(Align.center(HEADER_BANNER), border_style="cyan", expand=False))
    console.print(f" [bold dim]Manuscript:[/bold dim] [underline]{Path(tex_path).name}[/underline] | [bold dim]Bibliography:[/bold dim] [underline]{Path(bib_path).name}[/underline] | [bold dim]Oracle:[/bold dim] [bold yellow]{mode}[/bold yellow]\n")

    pipeline = VerificationPipeline(
        bib_path=bib_path,
        tex_path=tex_path,
        output_dir=output_dir,
        oracle_mode=mode,
    )

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=40, style="dim", complete_style="bold green"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Executing 18-stage citation & claim verification pipeline...", total=100)
        report = asyncio.run(pipeline.run())
        progress.update(task, completed=100)

    integ = report.integrity
    console.print("\n[bold green]Audit Pipeline Completed Successfully![/bold green]\n")

    # Render Summary Dashboard Table
    table = Table(title="Scientific Citation Integrity Report", title_style="bold magenta", header_style="bold cyan", border_style="dim")
    table.add_column("Metric", style="bold white", width=36)
    table.add_column("Value / Count", style="bold yellow", justify="right")
    table.add_column("Status / Rating", style="bold green")

    readiness = integ.publication_readiness_score * 100
    readiness_badge = "[bold green]HIGH READINESS[/bold green]" if readiness >= 75 else ("[bold yellow]MODERATE[/bold yellow]" if readiness >= 50 else "[bold red]ACTION REQUIRED[/bold red]")
    table.add_row("Publication Readiness Score", f"{readiness:.1f}%", readiness_badge)

    bib_q = integ.bibliography_quality_score * 100
    bib_badge = "[green]EXCELLENT[/green]" if bib_q >= 80 else ("[yellow]CORRECTIONS MADE[/yellow]" if bib_q >= 40 else "[red]NEEDS REPAIR[/red]")
    table.add_row("Bibliography Quality Score", f"{bib_q:.1f}%", bib_badge)

    cit_q = integ.citation_quality_score * 100
    cit_badge = "[green]VERIFIED SUPPORTED[/green]" if cit_q >= 90 else "[yellow]UNSUPPORTED CLAIMS[/yellow]"
    table.add_row("Citation Claim Integrity Score", f"{cit_q:.1f}%", cit_badge)

    table.add_section()
    table.add_row("Total References Audited", str(integ.total_references), "100% Processed")
    table.add_row("Verified High-Confidence Entries", str(integ.verified_count), f"[dim]{integ.verified_count}/{integ.total_references} entries[/dim]")
    table.add_row("Corrected Metadata Fields", str(integ.corrected_count), "[yellow]Updated in references_corrected.bib[/yellow]")
    table.add_row("Unsupported / Contradicted Claims", str(integ.unsupported_claims + integ.contradicted_claims), "[green]0 Discrepancies[/green]" if (integ.unsupported_claims + integ.contradicted_claims) == 0 else "[red]Review Required[/red]")

    console.print(table)

    output_path = Path(output_dir).resolve()
    console.print(Panel(
        f"[bold white]Generated Audit Artifacts:[/bold white]\n"
        f" Markdown Report: {output_path / 'report.md'}\n"
        f" HTML Dashboard:  {output_path / 'report.html'}\n"
        f" Corrected BibTeX: {output_path / 'references_corrected.bib'}\n"
        f" JSON & CSV Data: {output_path / 'report.json'}, {output_path / 'report.csv'}",
        border_style="green",
        title="Results Ready",
    ))

    if report.ai_queries_pending > 0:
        console.print(Panel(
            f"[bold yellow]Notice:[/bold yellow] {report.ai_queries_pending} queries pending AI Oracle review.\n"
            f"Run [bold cyan]scva ask --output-dir {output_dir}[/bold cyan] to inspect pending queries.",
            border_style="yellow",
        ))

    try:
        assets_dir = Path("assets")
        assets_dir.mkdir(exist_ok=True)
        console.save_svg(str(assets_dir / "terminal_audit.svg"), title="SCVA Citation Audit CLI")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ASK & INGEST COMMANDS
# ---------------------------------------------------------------------------

@main.command()
@click.option("--output-dir", "-o", default="./scva_output", help="Audit output directory.")
def ask(output_dir: str):
    """Inspect pending AI Oracle queries for delegation."""
    queries_file = Path(output_dir) / "ai_queries.json"
    if not queries_file.exists():
        console.print("[yellow]No pending ai_queries.json found in output directory.[/yellow]")
        return

    text = queries_file.read_text(encoding="utf-8", errors="replace")
    data = json.loads(text)
    queries = data.get("queries", [])
    console.print(f"\n[bold cyan]Pending AI Oracle Queries ({len(queries)}):[/bold cyan]\n")

    for q in queries:
        console.print(Panel(
            f"[bold yellow]ID:[/bold yellow] {q['query_id']} | [bold cyan]Type:[/bold cyan] {q['query_type']} | [bold green]Key:[/bold green] {q['citation_key']}\n"
            f"[dim]{q['instruction']}[/dim]",
            border_style="dim",
        ))


@main.command()
@click.argument("response_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./scva_output", help="Audit output directory.")
def ingest_response(response_path: str, output_dir: str):
    """Ingest answered AI Oracle responses from JSON file."""
    oracle = FileBasedOracle(Path(output_dir))
    count = oracle.ingest(Path(response_path))
    console.print(f"[bold green]Ingested {count} AI Oracle responses successfully![/bold green]")


# ---------------------------------------------------------------------------
# CONFIG COMMAND GROUP
# ---------------------------------------------------------------------------

@main.group()
def config():
    """Manage SCVA configuration, API keys, and default providers."""
    pass


@config.command("show")
def config_show():
    """Display current SCVA settings and configured API keys (secrets masked)."""
    cfg = ConfigManager()
    safe = cfg.show()

    table = Table(title="SCVA Configuration Settings", title_style="bold magenta", border_style="cyan")
    table.add_column("Category / Provider", style="bold white")
    table.add_column("Setting / Key Status", style="bold yellow")

    table.add_row("Default Oracle Provider", safe["default_oracle"])
    table.add_section()

    for k, v in safe["api_keys"].items():
        status = f"[green]{v}[/green]" if v and "Not set" not in v else "[dim]Not set[/dim]"
        table.add_row(f"API Key: {k}", status)

    table.add_section()
    for k, v in safe["default_models"].items():
        table.add_row(f"Default Model: {k}", v)

    console.print(table)


@config.command("set-key")
@click.argument("provider")
@click.argument("key")
def config_set_key(provider: str, key: str):
    """Securely store an API key (e.g. gemini, openai, claude, deepseek, moonshot, openrouter)."""
    cfg = ConfigManager()
    cfg.set_key(provider, key)
    console.print(f"[bold green]Saved API key for '{provider}' successfully![/bold green]")


@config.command("set-default-oracle")
@click.argument("oracle_name")
def config_set_default_oracle(oracle_name: str):
    """Set default oracle provider (antigravity, gemini, openai, claude, deepseek, moonshot, ollama)."""
    cfg = ConfigManager()
    cfg.set_default_oracle(oracle_name)
    console.print(f"[bold green]Default oracle provider set to '{oracle_name}'![/bold green]")


@config.command("set-model")
@click.argument("provider")
@click.argument("model_name")
def config_set_model(provider: str, model_name: str):
    """Set default model for a specific provider (e.g. set-model deepseek deepseek-reasoner)."""
    cfg = ConfigManager()
    cfg.set_model(provider, model_name)
    console.print(f"[bold green]Default model for '{provider}' set to '{model_name}'![/bold green]")


if __name__ == "__main__":
    main()

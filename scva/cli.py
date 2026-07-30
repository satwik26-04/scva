"""
Command Line Interface (CLI) for SCVA built with Click and Rich.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import ConfigManager
from .pipeline import VerificationPipeline
from .oracle import FileBasedOracle

console = Console()


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

    console.print(Panel(
        f"[bold cyan]Scientific Citation Verification Agent (SCVA)[/bold cyan]\n"
        f"Starting 18-stage citation audit...\n"
        f"[dim]Oracle Mode: [bold yellow]{mode}[/bold yellow] | Output: [underline]{output_dir}[/underline][/dim]"
    ))

    pipeline = VerificationPipeline(
        bib_path=bib_path,
        tex_path=tex_path,
        output_dir=output_dir,
        oracle_mode=mode,
    )

    with console.status("[bold green]Running audit pipeline...[/bold green]"):
        report = asyncio.run(pipeline.run())

    integ = report.integrity
    console.print("\n[bold green]Audit Completed Successfully![/bold green]\n")

    table = Table(title="Scientific Citation Integrity Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row("Publication Readiness Score", f"{integ.publication_readiness_score * 100:.1f}%")
    table.add_row("Bibliography Quality Score", f"{integ.bibliography_quality_score * 100:.1f}%")
    table.add_row("Citation Quality Score", f"{integ.citation_quality_score * 100:.1f}%")
    table.add_row("Total References", str(integ.total_references))
    table.add_row("Verified References", str(integ.verified_count))
    table.add_row("Corrected Metadata Entries", str(integ.corrected_count))
    table.add_row("Unsupported / Contradicted Claims", str(integ.unsupported_claims + integ.contradicted_claims))

    console.print(table)
    console.print(f"\n[bold yellow]Report Artifacts Written To:[/bold yellow] [underline]{Path(output_dir).resolve()}[/underline]\n")

    if report.ai_queries_pending > 0:
        console.print(f"[bold red]Note:[/bold red] {report.ai_queries_pending} queries pending AI Oracle review. Run `scva ask` or check `ai_queries.json` to review.")


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
    console.print(f"[bold cyan]Pending AI Queries ({len(queries)}):[/bold cyan]\n")

    for q in queries:
        console.print(f"[bold]Query ID:[/bold] {q['query_id']} | [bold]Type:[/bold] {q['query_type']} | [bold]Key:[/bold] {q['citation_key']}")
        console.print(f"[dim]{q['instruction']}[/dim]\n")


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

    console.print(Panel(
        f"[bold cyan]SCVA Configuration[/bold cyan]\n"
        f"Default Oracle: [bold yellow]{safe['default_oracle']}[/bold yellow]\n\n"
        f"[bold]Configured API Keys:[/bold]\n"
        + "\n".join(f"  {k}: {v or '[dim]Not set[/dim]'}" for k, v in safe["api_keys"].items())
        + "\n\n[bold]Default Models:[/bold]\n"
        + "\n".join(f"  {k}: {v}" for k, v in safe["default_models"].items())
        + "\n\n[bold]Custom Endpoints:[/bold]\n"
        + "\n".join(f"  {k}: {v}" for k, v in safe["custom_endpoints"].items())
    ))


@config.command("set-key")
@click.argument("provider")
@click.argument("key")
def config_set_key(provider: str, key: str):
    """Securely store an API key (e.g. gemini, openai, claude, openrouter, semantic_scholar, glm)."""
    cfg = ConfigManager()
    cfg.set_key(provider, key)
    console.print(f"[bold green]Saved API key for '{provider}' successfully![/bold green]")


@config.command("set-default-oracle")
@click.argument("oracle_name")
def config_set_default_oracle(oracle_name: str):
    """Set default oracle provider (antigravity, gemini, openai, claude, ollama, openrouter, nanogpt, glm)."""
    cfg = ConfigManager()
    cfg.set_default_oracle(oracle_name)
    console.print(f"[bold green]Default oracle provider set to '{oracle_name}'![/bold green]")


@config.command("set-model")
@click.argument("provider")
@click.argument("model_name")
def config_set_model(provider: str, model_name: str):
    """Set default model for a specific provider (e.g. set-model ollama llama3.2)."""
    cfg = ConfigManager()
    cfg.set_model(provider, model_name)
    console.print(f"[bold green]Default model for '{provider}' set to '{model_name}'![/bold green]")


@config.command("set-endpoint")
@click.argument("endpoint_name")
@click.argument("url")
def config_set_endpoint(endpoint_name: str, url: str):
    """Set custom endpoint URL (e.g. set-endpoint ollama_base_url http://localhost:11434)."""
    cfg = ConfigManager()
    cfg.set_endpoint(endpoint_name, url)
    console.print(f"[bold green]Custom endpoint '{endpoint_name}' set to '{url}'![/bold green]")


if __name__ == "__main__":
    main()

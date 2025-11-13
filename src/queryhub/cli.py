"""Command-line interface for QueryHub."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from .email.client import EmailClient
from .services import ReportExecutionResult, ReportExecutor

_LOGGER = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="QueryHub automation CLI")


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@app.command("run-report")
def run_report(
    report_id: str = typer.Argument(..., help="Identifier of the report to execute"),
    config_dir: Path = typer.Option(Path("config"), exists=True, file_okay=False, help="Configuration directory"),
    templates_dir: Path = typer.Option(Path("templates"), exists=True, file_okay=False, help="Directory containing Jinja templates"),
    output_html: Optional[Path] = typer.Option(None, help="Optional path to write the rendered HTML"),
    email: bool = typer.Option(True, help="Send the rendered report via SMTP"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Execute a report definition and optionally send it via email."""

    configure_logging(verbose)
    result = asyncio.run(_run_report(report_id, config_dir, templates_dir, output_html, email))
    if result.has_failures:
        raise typer.Exit(code=1)


async def _run_report(
    report_id: str,
    config_dir: Path,
    templates_dir: Path,
    output_html: Optional[Path],
    email: bool,
) -> ReportExecutionResult:
    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
        auto_reload_templates=False,
    )
    try:
        result = await executor.execute_report(report_id)
        if output_html:
            output_html.write_text(result.html, encoding="utf-8")
            typer.echo(f"Report written to {output_html}")

        typer.echo(f"Report '{result.report.title}' generated at {result.generated_at.isoformat()}")

        if email:
            smtp_client = EmailClient(executor.smtp_config)
            overrides = result.report.email
            await smtp_client.send_report(result, overrides=overrides)
            typer.echo("Report email sent")

        if result.has_failures:
            typer.echo("Report completed with component failures", err=True)
        return result
    finally:
        await executor.shutdown()


@app.command("list-reports")
def list_reports(
    config_dir: Path = typer.Option(Path("config"), exists=True, file_okay=False, help="Configuration directory"),
    templates_dir: Path = typer.Option(Path("templates"), exists=True, file_okay=False, help="Directory containing Jinja templates"),
) -> None:
    """List available report definitions."""

    async def _list() -> None:
        executor = await ReportExecutor.from_config_dir(
            config_dir,
            templates_dir=templates_dir,
        )
        try:
            for report_id, report in executor.settings.reports.items():
                typer.echo(f"{report_id}\t{report.title}")
        finally:
            await executor.shutdown()

    asyncio.run(_list())

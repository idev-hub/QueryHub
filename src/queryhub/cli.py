"""Command-line interface for QueryHub."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from .core.errors import QueryHubError
from .email.client import EmailClient
from .services import QueryHubApplicationBuilder, ReportExecutionResult

_LOGGER = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="QueryHub automation CLI")


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@app.command("run-report")
def run_report(
    report_id: str = typer.Argument(..., help="Identifier of the report to execute"),
    config_dir: Path = typer.Option(
        Path("config"), exists=True, file_okay=False, help="Configuration directory"
    ),
    templates_dir: Path = typer.Option(
        Path("templates"), exists=True, file_okay=False, help="Directory containing Jinja templates"
    ),
    output_html: Optional[Path] = typer.Option(
        None, help="Optional path to write the rendered HTML"
    ),
    email: bool = typer.Option(True, help="Send the rendered report via SMTP"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Execute a report definition and optionally send it via email."""
    configure_logging(verbose)
    _LOGGER.info("Starting QueryHub report execution for report_id='%s'", report_id)
    _LOGGER.debug("Configuration: config_dir=%s, templates_dir=%s", config_dir, templates_dir)

    try:
        result = asyncio.run(_run_report(report_id, config_dir, templates_dir, output_html, email))
        if result.has_failures:
            _LOGGER.warning("Report execution completed with failures")
            raise typer.Exit(code=1)
        _LOGGER.info("Report execution completed successfully")
    except QueryHubError as exc:
        _LOGGER.error("Report execution failed: %s", exc, exc_info=verbose)
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


async def _run_report(
    report_id: str,
    config_dir: Path,
    templates_dir: Path,
    output_html: Optional[Path],
    email: bool,
) -> ReportExecutionResult:
    """Execute report with proper resource management."""
    _LOGGER.info("Initializing QueryHub application builder")
    builder = QueryHubApplicationBuilder(
        config_dir=config_dir,
        templates_dir=templates_dir,
        auto_reload_templates=False,
    )
    _LOGGER.debug("Creating report executor")
    executor = await builder.create_executor()

    try:
        _LOGGER.info("Executing report: %s", report_id)
        result = await executor.execute_report(report_id)

        if output_html:
            _LOGGER.info("Writing report HTML to file: %s", output_html)
            output_html.write_text(result.html, encoding="utf-8")
            typer.echo(f"Report written to {output_html}")

        typer.echo(f"Report '{result.report.title}' generated at {result.generated_at.isoformat()}")
        _LOGGER.info(
            "Report '%s' completed: %d/%d components successful",
            result.report.title,
            result.success_count,
            len(result.components),
        )

        if email:
            _LOGGER.info("Sending report via email")
            smtp_client = EmailClient(executor.smtp_config)
            overrides = result.report.email
            await smtp_client.send_report(result, overrides=overrides)
            typer.echo("Report email sent")
            _LOGGER.info("Email sent successfully")

        if result.has_failures:
            failed_ids = [c.component.id for c in result.components if not c.is_success]
            _LOGGER.warning("Report completed with component failures: %s", failed_ids)
            typer.echo("Report completed with component failures", err=True)

        return result
    finally:
        _LOGGER.debug("Shutting down executor and cleaning up resources")
        await executor.shutdown()


@app.command("list-reports")
def list_reports(
    config_dir: Path = typer.Option(
        Path("config"), exists=True, file_okay=False, help="Configuration directory"
    ),
    templates_dir: Path = typer.Option(
        Path("templates"), exists=True, file_okay=False, help="Directory containing Jinja templates"
    ),
) -> None:
    """List available report definitions."""
    asyncio.run(_list_reports(config_dir, templates_dir))


async def _list_reports(config_dir: Path, templates_dir: Path) -> None:
    """List all configured reports."""
    _LOGGER.info("Loading report configurations from: %s", config_dir)
    builder = QueryHubApplicationBuilder(
        config_dir=config_dir,
        templates_dir=templates_dir,
    )
    executor = await builder.create_executor()

    try:
        report_count = len(executor.settings.reports)
        _LOGGER.info("Found %d configured report(s)", report_count)
        for report_id, report in executor.settings.reports.items():
            typer.echo(f"{report_id}\t{report.title}")
    finally:
        await executor.shutdown()

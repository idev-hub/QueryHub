"""Command-line interface for QueryHub."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
import yaml

from .core.errors import QueryHubError
from .email.client import EmailClient
from .services import QueryHubApplicationBuilder, ReportExecutionResult

_LOGGER = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="QueryHub automation CLI")


def find_metadata_file(folder: Path) -> Path:
    """Find metadata file with .yaml or .yml extension.
    
    Args:
        folder: Directory containing the metadata file
        
    Returns:
        Path to the metadata file
        
    Raises:
        FileNotFoundError: If no metadata file is found
    """
    for ext in (".yaml", ".yml"):
        metadata_path = folder / f"metadata{ext}"
        if metadata_path.exists():
            return metadata_path
    raise FileNotFoundError(f"No metadata.yaml or metadata.yml found in {folder}")


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@app.command("run-report")
def run_report(
    report_folder: Path = typer.Argument(..., help="Path to the report folder containing metadata.yaml and components", exists=True, file_okay=False, dir_okay=True),
    output_html: Optional[Path] = typer.Option(
        None, help="Optional path to write the rendered HTML"
    ),
    email: bool = typer.Option(True, help="Send the rendered report via SMTP"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Execute a report from a folder and optionally send it via email.
    
    The report folder should contain:
    - metadata.yaml: Report configuration
    - 01_component.yaml, 02_component.yaml, etc.: Numbered component files
    
    Templates and providers are auto-discovered from the config structure.
    """
    configure_logging(verbose)
    _LOGGER.info("Starting QueryHub report execution from folder: %s", report_folder)

    try:
        result = asyncio.run(_run_report_folder(report_folder, output_html, email))
        if result.has_failures:
            _LOGGER.warning("Report execution completed with failures")
            raise typer.Exit(code=1)
        _LOGGER.info("Report execution completed successfully")
    except QueryHubError as exc:
        _LOGGER.error("Report execution failed: %s", exc, exc_info=verbose)
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


async def _run_report_folder(
    report_folder: Path,
    output_html: Optional[Path],
    email: bool,
) -> ReportExecutionResult:
    """Execute report from folder with proper resource management."""
    from .config.loader import ConfigLoader
    
    _LOGGER.info("Loading report from folder: %s", report_folder)
    
    # Auto-discover config structure from report folder
    # Report folder structure: config/reports/report_name/
    config_root = report_folder.parent.parent  # Go up to config/
    
    _LOGGER.debug("Config root: %s", config_root)
    
    # Resolve template and providers folders
    metadata_path = find_metadata_file(report_folder)
    metadata_data = yaml.safe_load(metadata_path.read_text())
    template_folder_override = metadata_data.get("template_folder")
    providers_folder_override = metadata_data.get("providers_folder")
    smtp_config_name = metadata_data.get("smtp_config")
    
    templates_dir = ConfigLoader.resolve_template_folder(report_folder, template_folder_override)
    providers_dir = ConfigLoader.resolve_providers_folder(report_folder, providers_folder_override)
    smtp_file = ConfigLoader.resolve_smtp_config_path(report_folder, smtp_config_name)
    
    _LOGGER.debug("Templates directory: %s", templates_dir)
    _LOGGER.debug("Providers directory: %s", providers_dir)
    _LOGGER.debug("SMTP config: %s", smtp_file)
    
    # Validate SMTP config for email mode
    if email and smtp_file is None:
        _LOGGER.error("Email mode requested but no SMTP configuration found")
        raise typer.BadParameter(
            "Email mode requires SMTP configuration. "
            "Either add 'smtp_config' to metadata.yaml or create config/smtp/default.yaml"
        )
    
    # Load configuration
    loader = ConfigLoader(config_root)
    report_config = loader.load_report_from_folder(report_folder)
    
    # Load SMTP settings if available
    smtp_config = None
    if smtp_file:
        smtp_data = loader._load_and_substitute_file(smtp_file)
        from .config.models import SMTPConfig
        smtp_config = SMTPConfig.model_validate(smtp_data or {})
    else:
        # HTML-only mode: create minimal SMTP config
        from .config.models import SMTPConfig
        smtp_config = SMTPConfig.model_validate({})
    
    # Load providers
    providers_data = loader._load_and_substitute_providers(providers_dir)
    providers = loader._parser.parse_providers(providers_data)
    
    _LOGGER.info("Initializing QueryHub application builder")
    builder = QueryHubApplicationBuilder(
        config_dir=config_root,
        templates_dir=templates_dir,
        auto_reload_templates=False,
    )
    _LOGGER.debug("Creating report executor")
    executor = await builder.create_executor()
    
    # Override settings with loaded configuration
    executor.settings.reports[report_config.id] = report_config
    executor.settings.providers.update(providers)
    executor.settings.smtp = smtp_config

    try:
        _LOGGER.info("Executing report: %s", report_config.id)
        result = await executor.execute_report(report_config.id)

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
    config_dir: Path = typer.Argument(Path("config"), exists=True, file_okay=False, help="Configuration directory containing reports/"),
) -> None:
    """List available report definitions."""
    asyncio.run(_list_reports(config_dir))


async def _list_reports(config_dir: Path) -> None:
    """List all configured reports."""
    _LOGGER.info("Loading report configurations from: %s", config_dir)
    
    reports_dir = config_dir / "reports"
    if not reports_dir.exists():
        typer.echo(f"No reports directory found at: {reports_dir}", err=True)
        return
    
    # List all report folders
    report_folders = [f for f in reports_dir.iterdir() if f.is_dir()]
    
    if not report_folders:
        typer.echo("No reports found")
        return
    
    _LOGGER.info("Found %d report folder(s)", len(report_folders))
    for report_folder in sorted(report_folders):
        try:
            metadata_path = find_metadata_file(report_folder)
            metadata = yaml.safe_load(metadata_path.read_text())
            report_id = metadata.get("id", report_folder.name)
            report_title = metadata.get("title", "No title")
            typer.echo(f"{report_id}\t{report_title}")
        except FileNotFoundError:
            _LOGGER.debug("Skipping folder without metadata: %s", report_folder)
            continue
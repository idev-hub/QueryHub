"""Integration tests for the report executor."""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path

import pytest
from aiohttp import web

from queryhub.services import QueryHubApplicationBuilder


@pytest.mark.asyncio
async def test_execute_csv_report(monkeypatch) -> None:
    config_dir = Path("tests/fixtures/config_basic")
    templates_dir = Path("config/templates")
    csv_root = Path("tests/fixtures/data").resolve()
    monkeypatch.setenv("CSV_ROOT", str(csv_root))

    builder = QueryHubApplicationBuilder(
        config_dir=config_dir,
        templates_dir=templates_dir,
    )
    executor = await builder.create_executor()
    try:
        # Load the csv_only report
        from queryhub.config.loader import ConfigLoader
        loader = ConfigLoader(config_dir)
        report_config = loader.load_report_from_folder(config_dir / "reports" / "csv_only")
        executor.settings.reports[report_config.id] = report_config
        
        result = await executor.execute_report(report_config.id)
    finally:
        await executor.shutdown()

    assert "CSV Fixture Report" in result.html
    assert "Sample Data Table" in result.html
    assert not result.has_failures


@pytest.mark.asyncio
async def test_execute_sql_and_rest_report(monkeypatch, tmp_path) -> None:
    config_dir = tmp_path / "config"
    providers_dir = config_dir / "providers"
    reports_dir = config_dir / "reports"
    smtp_dir = config_dir / "smtp"
    providers_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    smtp_dir.mkdir(parents=True)

    smtp_yaml = textwrap.dedent(
        """
        host: localhost
        port: 1025
        use_tls: false
        starttls: false
        default_from: reports@example.test
        """
    )
    (smtp_dir / "default.yaml").write_text(smtp_yaml, encoding="utf-8")

    db_path = tmp_path / "metrics.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE metrics (category TEXT, total INTEGER)")
        conn.execute("INSERT INTO metrics VALUES ('alpha', 42)")
        conn.execute("INSERT INTO metrics VALUES ('beta', 7)")
        conn.commit()

    sqlite_dsn = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("SQLITE_DSN", sqlite_dsn)

    app = web.Application()

    async def _handle_data(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "total": 99})

    app.router.add_get("/data", _handle_data)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sockets = site._server.sockets  # type: ignore[attr-defined]
    assert sockets
    port = sockets[0].getsockname()[1]
    base_url = f"http://127.0.0.1:{port}/"
    monkeypatch.setenv("REST_BASE_URL", base_url)

    providers_yaml = textwrap.dedent(
        """\
        providers:
          - id: sqlite_metrics
            resource:
              sql:
                dsn: ${SQLITE_DSN}
          - id: rest_local
            resource:
              rest:
                base_url: ${REST_BASE_URL}
                default_headers:
                  Accept: application/json
        """
    )
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    # Create folder-based report
    combined_dir = reports_dir / "combined_report"
    combined_dir.mkdir()
    
    metadata_yaml = textwrap.dedent(
        """\
        id: combined_report
        title: SQL and REST Report
        template: report.html.j2
        email:
          to:
            - qa@example.test
        """
    )
    (combined_dir / "metadata.yaml").write_text(metadata_yaml, encoding="utf-8")
    
    component1_yaml = textwrap.dedent(
        """\
        id: metrics_table
        provider: sqlite_metrics
        query:
          text: |
            SELECT category, total FROM metrics ORDER BY total DESC
        render:
          type: table
        """
    )
    (combined_dir / "01_metrics.yaml").write_text(component1_yaml, encoding="utf-8")
    
    component2_yaml = textwrap.dedent(
        """\
        id: api_status
        provider: rest_local
        query:
          endpoint: data
        render:
          type: text
          options:
            template: "API status: {value}"
            value_path: status
        """
    )
    (combined_dir / "02_api.yaml").write_text(component2_yaml, encoding="utf-8")

    builder = QueryHubApplicationBuilder(
        config_dir=config_dir,
        templates_dir=Path("config/templates"),
    )
    executor = None
    try:
        executor = await builder.create_executor()
        # Load the report from folder
        from queryhub.config.loader import ConfigLoader
        loader = ConfigLoader(config_dir)
        report_config = loader.load_report_from_folder(combined_dir)
        executor.settings.reports[report_config.id] = report_config
        
        result = await executor.execute_report("combined_report")
    finally:
        if executor is not None:
            await executor.shutdown()
        await runner.cleanup()

    assert not result.has_failures
    assert len(result.components) == 2

    metrics_component = next(
        item for item in result.components if item.component.id == "metrics_table"
    )
    assert metrics_component.result is not None
    assert metrics_component.result.data[0]["category"] == "alpha"

    rest_component = next(item for item in result.components if item.component.id == "api_status")
    assert rest_component.rendered_html is not None
    assert "API status: ok" in rest_component.rendered_html

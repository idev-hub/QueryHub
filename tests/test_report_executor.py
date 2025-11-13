"""Integration tests for the report executor."""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path

import pytest
from aiohttp import web

from queryhub.services import ReportExecutor


@pytest.mark.asyncio
async def test_execute_csv_report(monkeypatch) -> None:
    config_dir = Path("tests/fixtures/config_basic")
    templates_dir = Path("templates")
    csv_root = Path("tests/fixtures/data").resolve()
    monkeypatch.setenv("CSV_ROOT", str(csv_root))

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )
    try:
        result = await executor.execute_report("csv_only")
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
    providers_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)

    smtp_yaml = textwrap.dedent(
        """\
        host: localhost
        port: 1025
        use_tls: false
        starttls: false
        default_from: reports@example.test
        """
    )
    (config_dir / "smtp.yaml").write_text(smtp_yaml, encoding="utf-8")

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
            type: sql
            target:
              dsn: ${SQLITE_DSN}
          - id: rest_local
            type: rest
            base_url: ${REST_BASE_URL}
            default_headers:
              Accept: application/json
        """
    )
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    report_yaml = textwrap.dedent(
        """\
        id: combined_report
        title: SQL and REST Report
        template: report.html.j2
        components:
          - id: metrics_table
            provider: sqlite_metrics
            query:
              text: |
                SELECT category, total FROM metrics ORDER BY total DESC
            render:
              type: table
          - id: api_status
            provider: rest_local
            query:
              endpoint: data
            render:
              type: text
              options:
                template: "API status: {value}"
                value_path: status
        email:
          to:
            - qa@example.test
        """
    )
    (reports_dir / "combined.yaml").write_text(report_yaml, encoding="utf-8")

    templates_dir = Path("templates")
    executor: ReportExecutor | None = None
    try:
        executor = await ReportExecutor.from_config_dir(
            config_dir,
            templates_dir=templates_dir,
        )
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

    rest_component = next(
        item for item in result.components if item.component.id == "api_status"
    )
    assert rest_component.rendered_html is not None
    assert "API status: ok" in rest_component.rendered_html

"""Docker-based integration tests for QueryHub.

This module contains integration tests that use Docker containers to test
the full pipeline: database setup, query execution, and HTML report rendering.

Prerequisites:
    - Docker and Docker Compose installed
    - Run: docker-compose -f docker-compose.test.yml up -d

Usage:
    pytest tests/test_docker_integration.py -v
    pytest tests/test_docker_integration.py::test_postgres_sales_report -v
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

import pytest

from queryhub.services import ReportExecutor


def is_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def are_containers_running() -> bool:
    """Check if test containers are running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=queryhub-test-postgres", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return "queryhub-test-postgres" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def wait_for_postgres(max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Wait for PostgreSQL container to be healthy."""
    import asyncpg

    dsn = "postgresql://testuser:testpass@localhost:5434/testdb"

    for attempt in range(max_attempts):
        try:
            # Try to connect synchronously
            import asyncio

            async def check():
                conn = await asyncpg.connect(dsn)
                await conn.close()

            asyncio.run(check())
            return True
        except Exception:  # noqa: BLE001
            if attempt < max_attempts - 1:
                time.sleep(delay)
            continue
    return False


@pytest.fixture(scope="module")
def docker_available() -> bool:
    """Check if Docker is available for integration tests."""
    return is_docker_running()


@pytest.fixture(scope="module")
def containers_ready(docker_available: bool) -> bool:
    """Ensure Docker containers are running and ready."""
    if not docker_available:
        pytest.skip("Docker is not running")

    if not are_containers_running():
        pytest.skip(
            "Test containers are not running. "
            "Start them with: docker-compose -f docker-compose.test.yml up -d"
        )

    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        pytest.skip("PostgreSQL container failed to become ready")

    return True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_connection(containers_ready: bool, monkeypatch) -> None:
    """Test basic PostgreSQL connection and query execution."""
    import asyncpg

    dsn = "postgresql://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    conn = await asyncpg.connect(dsn)
    try:
        # Test basic query
        result = await conn.fetch("SELECT 1 as test")
        assert len(result) == 1
        assert result[0]["test"] == 1

        # Test that our schema exists
        tables = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )
        table_names = [row["table_name"] for row in tables]
        assert "sales_metrics" in table_names
        assert "customer_feedback" in table_names
        assert "system_health" in table_names

        # Test that we have data
        count = await conn.fetchval("SELECT COUNT(*) FROM sales_metrics")
        assert count > 0
    finally:
        await conn.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_sales_report(containers_ready: bool, monkeypatch, tmp_path) -> None:
    """Test full report execution with PostgreSQL backend."""
    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("sales_dashboard")
    finally:
        await executor.shutdown()

    # Verify report was generated successfully
    assert result is not None
    assert not result.has_failures
    assert result.html is not None
    assert len(result.html) > 0

    # Save rendered HTML for inspection
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "sales_dashboard_report.html"
    output_file.write_text(result.html, encoding="utf-8")
    print(f"\n✅ Report saved to: {output_file.absolute()}")

    # Check that report contains expected content
    assert "Sales & Health Dashboard" in result.html
    assert "Sales by Region" in result.html
    assert "Product Performance" in result.html
    assert "Customer Satisfaction Summary" in result.html
    assert "System Health Status" in result.html

    # Verify components executed successfully
    assert len(result.components) == 5

    # Check sales_by_region component
    sales_component = next(
        (c for c in result.components if c.component.id == "sales_by_region"),
        None,
    )
    assert sales_component is not None
    assert sales_component.result is not None
    assert len(sales_component.result.data) > 0
    assert "region" in sales_component.result.data[0]
    assert "total_revenue" in sales_component.result.data[0]

    # Check product_performance component
    product_component = next(
        (c for c in result.components if c.component.id == "product_performance"),
        None,
    )
    assert product_component is not None
    assert product_component.result is not None
    assert len(product_component.result.data) > 0

    # Check customer_satisfaction component
    satisfaction_component = next(
        (c for c in result.components if c.component.id == "customer_satisfaction"),
        None,
    )
    assert satisfaction_component is not None
    assert satisfaction_component.result is not None
    assert len(satisfaction_component.result.data) > 0
    assert "avg_rating" in satisfaction_component.result.data[0]

    # Check system_health component
    health_component = next(
        (c for c in result.components if c.component.id == "system_health"),
        None,
    )
    assert health_component is not None
    assert health_component.result is not None
    assert len(health_component.result.data) > 0
    assert "service_name" in health_component.result.data[0]
    assert "status" in health_component.result.data[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_query_with_parameters(
    containers_ready: bool, monkeypatch, tmp_path
) -> None:
    """Test SQL queries with parameters."""
    import textwrap

    config_dir = tmp_path / "config"
    providers_dir = config_dir / "providers"
    reports_dir = config_dir / "reports"
    providers_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    # Create config files
    smtp_yaml = textwrap.dedent(
        """\
        host: localhost
        port: 1025
        use_tls: false
        starttls: false
        default_from: reports@test.local
        """
    )
    (config_dir / "smtp.yaml").write_text(smtp_yaml, encoding="utf-8")

    providers_yaml = textwrap.dedent(
        """\
        providers:
          - id: postgres_test
            resource:
              sql:
                dsn: ${POSTGRES_DSN}
        """
    )
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    report_yaml = textwrap.dedent(
        """\
        id: parameterized_report
        title: Sales Report with Parameters
        template: report.html.j2
        components:
          - id: filtered_sales
            title: Sales by Region
            provider: postgres_test
            query:
              text: |
                SELECT region, product, revenue, units_sold
                FROM sales_metrics
                WHERE region = :target_region
                ORDER BY revenue DESC
              parameters:
                target_region: "North America"
            render:
              type: table
        email:
          to:
            - test@example.com
        """
    )
    (reports_dir / "param_test.yaml").write_text(report_yaml, encoding="utf-8")

    templates_dir = Path("templates")
    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("parameterized_report")
    finally:
        await executor.shutdown()

    assert not result.has_failures
    assert len(result.components) == 1

    component = result.components[0]
    assert component.result is not None
    assert len(component.result.data) > 0

    # Verify all results are from North America
    for row in component.result.data:
        assert row["region"] == "North America"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_aggregation_queries(containers_ready: bool, monkeypatch, tmp_path) -> None:
    """Test complex aggregation queries."""
    import textwrap

    config_dir = tmp_path / "config"
    providers_dir = config_dir / "providers"
    reports_dir = config_dir / "reports"
    providers_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    smtp_yaml = textwrap.dedent(
        """\
        host: localhost
        port: 1025
        use_tls: false
        starttls: false
        default_from: reports@test.local
        """
    )
    (config_dir / "smtp.yaml").write_text(smtp_yaml, encoding="utf-8")

    providers_yaml = textwrap.dedent(
        """\
        providers:
          - id: postgres_test
            resource:
              sql:
                dsn: ${POSTGRES_DSN}
        """
    )
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    report_yaml = textwrap.dedent(
        """\
        id: aggregation_report
        title: Advanced Analytics Report
        template: report.html.j2
        components:
          - id: revenue_stats
            title: Revenue Statistics
            provider: postgres_test
            query:
              text: |
                SELECT 
                  COUNT(DISTINCT region) as region_count,
                  COUNT(DISTINCT product) as product_count,
                  SUM(revenue) as total_revenue,
                  AVG(revenue) as avg_revenue,
                  MIN(revenue) as min_revenue,
                  MAX(revenue) as max_revenue,
                  SUM(units_sold) as total_units
                FROM sales_metrics
            render:
              type: table
          - id: top_products
            title: Top Products by Revenue
            provider: postgres_test
            query:
              text: |
                SELECT 
                  product,
                  SUM(revenue) as total_revenue,
                  COUNT(*) as transaction_count
                FROM sales_metrics
                GROUP BY product
                ORDER BY total_revenue DESC
            render:
              type: table
        email:
          to:
            - analytics@test.local
        """
    )
    (reports_dir / "agg_test.yaml").write_text(report_yaml, encoding="utf-8")

    templates_dir = Path("templates")
    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("aggregation_report")
    finally:
        await executor.shutdown()

    assert not result.has_failures
    assert len(result.components) == 2

    # Check revenue stats
    stats_component = result.components[0]
    assert stats_component.result is not None
    assert len(stats_component.result.data) == 1
    stats = stats_component.result.data[0]
    assert stats["region_count"] >= 3  # North America, Europe, Asia Pacific
    assert stats["product_count"] >= 2  # Widget Pro, Widget Lite
    assert stats["total_revenue"] > 0
    assert stats["total_units"] > 0

    # Check top products
    products_component = result.components[1]
    assert products_component.result is not None
    assert len(products_component.result.data) > 0
    # Results should be ordered by revenue DESC
    revenues = [row["total_revenue"] for row in products_component.result.data]
    assert revenues == sorted(revenues, reverse=True)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_queries(containers_ready: bool, monkeypatch) -> None:
    """Test executing multiple queries concurrently."""
    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        # Execute the same report multiple times concurrently
        tasks = [executor.execute_report("sales_dashboard") for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # Verify all reports completed successfully
        assert len(results) == 3
        for result in results:
            assert not result.has_failures
            assert len(result.components) == 5
    finally:
        await executor.shutdown()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_all_visualizations(containers_ready: bool, monkeypatch) -> None:
    """Test all available visualization types with real data."""
    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("all_visualizations")
    finally:
        await executor.shutdown()

    # Verify report was generated successfully
    assert result is not None
    assert not result.has_failures
    assert result.html is not None
    assert len(result.html) > 0

    # Save rendered HTML for inspection
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "all_visualizations_report.html"
    output_file.write_text(result.html, encoding="utf-8")
    print(f"\n✅ All visualizations report saved to: {output_file.absolute()}")

    # Verify all 15 components executed
    assert len(result.components) == 15

    # Verify each component type
    component_types = {c.component.render.type.value for c in result.components}
    assert "table" in component_types
    assert "text" in component_types
    assert "html" in component_types

    # Check that we have data in components
    for component_result in result.components:
        if component_result.result is not None:
            assert component_result.result.data is not None
        assert component_result.rendered_html is not None
        assert len(component_result.rendered_html) > 0

    # Verify specific components
    simple_table = next(c for c in result.components if c.component.id == "simple_table")
    assert simple_table.result is not None
    assert len(simple_table.result.data) > 0

    total_revenue_text = next(
        c for c in result.components if c.component.id == "total_revenue_text"
    )
    assert total_revenue_text.rendered_html is not None
    assert "Total Revenue:" in total_revenue_text.rendered_html

    transaction_count = next(c for c in result.components if c.component.id == "transaction_count")
    assert transaction_count.rendered_html is not None

    # Verify HTML components
    key_metrics = next(c for c in result.components if c.component.id == "key_metrics_card")
    assert key_metrics.rendered_html is not None
    assert "gradient" in key_metrics.rendered_html

    top_regions = next(c for c in result.components if c.component.id == "top_regions_list")
    assert top_regions.rendered_html is not None
    assert "transactions" in top_regions.rendered_html
    assert "Total Transactions:" in transaction_count.rendered_html

    # Check HTML content includes all sections
    assert "Simple Table - All Sales" in result.html
    assert "Aggregated Sales by Region" in result.html
    assert "Customer Feedback" in result.html
    assert "Total Revenue" in result.html
    assert "Transaction Count" in result.html
    assert "System Health" in result.html
    assert "Top 5 Products by Revenue" in result.html
    assert "Product Ratings" in result.html
    assert "Last 5 Transactions" in result.html
    assert "Overall Average Rating" in result.html

    print("\n📊 Component Summary:")
    for c in result.components:
        status = "✅" if c.result else "⚠️"
        print(f"  {status} {c.component.id} ({c.component.render.type.value})")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chart_visualizations(containers_ready: bool, monkeypatch) -> None:
    """Test chart rendering with Plotly visualizations."""
    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("chart_visualizations")
    finally:
        await executor.shutdown()

    # Verify report was generated successfully
    assert result is not None
    assert not result.has_failures
    assert result.html is not None
    assert len(result.html) > 0

    # Save rendered HTML for inspection
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "chart_visualizations_report.html"
    output_file.write_text(result.html, encoding="utf-8")
    print(f"\n✅ Chart visualizations report saved to: {output_file.absolute()}")

    # Verify all 8 components executed successfully (7 charts + 1 table)
    assert len(result.components) == 8

    # Check that chart components contain Plotly elements
    chart_components = [c for c in result.components if c.component.render.type.value == "chart"]
    assert len(chart_components) == 7

    for chart_component in chart_components:
        assert chart_component.result is not None
        assert len(chart_component.result.data) > 0
        assert chart_component.rendered_html is not None
        # Plotly charts should have plotly div elements
        assert "plotly" in chart_component.rendered_html.lower()

    # Verify specific chart components
    bar_chart = next(c for c in result.components if c.component.id == "revenue_by_region_bar")
    assert bar_chart.result is not None
    assert "region" in bar_chart.result.data[0]
    assert "total_revenue" in bar_chart.result.data[0]

    line_chart = next(c for c in result.components if c.component.id == "revenue_trend_line")
    assert line_chart.result is not None
    assert "date" in line_chart.result.data[0]
    assert "daily_revenue" in line_chart.result.data[0]

    scatter_plot = next(
        c for c in result.components if c.component.id == "units_vs_revenue_scatter"
    )
    assert scatter_plot.result is not None
    assert "units_sold" in scatter_plot.result.data[0]
    assert "revenue" in scatter_plot.result.data[0]
    assert "region" in scatter_plot.result.data[0]

    # Check table component still works
    table_component = next(c for c in result.components if c.component.id == "summary_stats_table")
    assert table_component.result is not None
    assert "total_transactions" in table_component.result.data[0]

    # Verify HTML contains chart titles
    assert "Revenue by Region (Bar Chart)" in result.html
    assert "Revenue Trend Over Time (Line Chart)" in result.html
    assert "Units Sold vs Revenue (Scatter Plot)" in result.html
    assert "Product Performance by Region (Colored Bar Chart)" in result.html
    assert "Daily Transaction Count (Line Chart)" in result.html
    assert "Average Customer Rating by Product (Bar Chart)" in result.html
    assert "System Health - Response Time vs Errors (Scatter Plot)" in result.html

    print("\n📊 Chart Component Summary:")
    for c in result.components:
        status = "✅" if c.result else "⚠️"
        print(f"  {status} {c.component.id} ({c.component.render.type.value})")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chart_email_generation(containers_ready: bool, monkeypatch) -> None:
    """Test email generation with chart visualizations and save as .eml file."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import datetime

    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    # Use email_mode=True to render charts as static images
    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
        email_mode=True,
    )

    try:
        result = await executor.execute_report("chart_visualizations")
    finally:
        await executor.shutdown()

    assert result is not None
    assert not result.has_failures
    assert result.html is not None

    # Create email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "QueryHub - Chart Visualizations Report"
    msg["From"] = "queryhub@example.com"
    msg["To"] = "user@example.com"
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    # Add plain text version
    text_content = f"""
QueryHub Report: Chart Visualizations

This is an HTML email. Please view it in an email client that supports HTML.

Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Components: {len(result.components)}
Charts: 7 static images (email-compatible)
"""

    # Attach parts
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(result.html, "html")

    msg.attach(part1)
    msg.attach(part2)

    # Save as .eml file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    eml_file = output_dir / "chart_visualizations_email.eml"

    with open(eml_file, "w", encoding="utf-8") as f:
        f.write(msg.as_string())

    print(f"\n📧 Email saved to: {eml_file.absolute()}")
    print(f"📊 Components included: {len(result.components)}")
    print(f"📝 HTML size: {len(result.html):,} bytes")
    print("\n💡 To view the email:")
    print(f"   macOS: open {eml_file}")
    print(f"   Linux: xdg-open {eml_file}")
    print(f"   Windows: start {eml_file}")

    # Verify file was created and has content
    assert eml_file.exists()
    assert eml_file.stat().st_size > 0

    # Verify email structure
    email_content = eml_file.read_text(encoding="utf-8")
    assert "Subject: QueryHub - Chart Visualizations Report" in email_content
    assert "Content-Type: text/html" in email_content
    assert "Content-Type: text/plain" in email_content

    # Verify HTML contains static images (base64 encoded PNG)
    assert "data:image/png;base64," in result.html
    assert "Revenue by Region (Bar Chart)" in result.html


@pytest.mark.asyncio
@pytest.mark.integration
async def test_email_generation(containers_ready: bool, monkeypatch) -> None:
    """Test email generation with all visualizations and save as .eml file."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import datetime

    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")

    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    executor = await ReportExecutor.from_config_dir(
        config_dir,
        templates_dir=templates_dir,
    )

    try:
        result = await executor.execute_report("all_visualizations")
    finally:
        await executor.shutdown()

    assert result is not None
    assert not result.has_failures
    assert result.html is not None

    # Create email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "QueryHub - All Visualizations Report"
    msg["From"] = "queryhub@example.com"
    msg["To"] = "user@example.com"
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    # Add plain text version
    text_content = f"""
QueryHub Report: All Visualizations

This is an HTML email. Please view it in an email client that supports HTML.

Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Components: {len(result.components)}
"""

    # Attach parts
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(result.html, "html")

    msg.attach(part1)
    msg.attach(part2)

    # Save as .eml file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    eml_file = output_dir / "all_visualizations_email.eml"

    with open(eml_file, "w", encoding="utf-8") as f:
        f.write(msg.as_string())

    print(f"\n📧 Email saved to: {eml_file.absolute()}")
    print(f"📊 Components included: {len(result.components)}")
    print(f"📝 HTML size: {len(result.html):,} bytes")
    print("\n💡 To view the email:")
    print(f"   macOS: open {eml_file}")
    print(f"   Linux: xdg-open {eml_file}")
    print(f"   Windows: start {eml_file}")

    # Verify file was created and has content
    assert eml_file.exists()
    assert eml_file.stat().st_size > 0

    # Verify email structure
    email_content = eml_file.read_text(encoding="utf-8")
    assert "Subject: QueryHub - All Visualizations Report" in email_content
    assert "Content-Type: text/html" in email_content
    assert "Content-Type: text/plain" in email_content

    # Verify HTML content contains our custom visualizations
    assert "Key Performance Indicators" in result.html
    assert "gradient" in result.html


if __name__ == "__main__":
    # Helper for manual testing
    print("Docker Integration Test Helper")
    print("=" * 50)

    if not is_docker_running():
        print("❌ Docker is not running")
    else:
        print("✅ Docker is running")

    if are_containers_running():
        print("✅ Test containers are running")
        if wait_for_postgres(max_attempts=5):
            print("✅ PostgreSQL is ready")
        else:
            print("❌ PostgreSQL is not ready")
    else:
        print("❌ Test containers are not running")
        print("\nTo start containers, run:")
        print("  docker-compose -f docker-compose.test.yml up -d")
        print("\nTo stop containers, run:")
        print("  docker-compose -f docker-compose.test.yml down")

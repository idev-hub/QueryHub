# QueryHub

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Transform your data into beautiful, automated email reports — no code required.**

QueryHub solves the problem of creating and delivering data-driven email reports across your organization. Instead of writing custom scripts for each report, define your data sources, queries, and layouts in simple YAML configuration files. QueryHub handles the complexity of connecting to multiple databases, executing queries, rendering visualizations, and delivering professional HTML emails.

## 🎯 What Problem Does QueryHub Solve?

**The Challenge:** Your team needs regular reports from multiple data sources (databases, APIs, cloud services), but:
- Writing custom reporting scripts for each report is time-consuming
- Maintaining separate code for database connections, query execution, HTML rendering, and email delivery is complex
- Each new report or data source requires significant development effort
- Reports lack consistent styling and branding

**The Solution:** QueryHub provides a configuration-driven platform where you:
1. Define your data sources once (PostgreSQL, Azure Kusto, AWS resources, GCP BigQuery, REST APIs, CSV files)
2. Write SQL queries or data transformations in YAML
3. Choose from pre-built visualizations (tables, charts, KPI cards, alerts)
4. Let QueryHub handle connections, authentication, rendering, and email delivery

## ✨ Key Features

### 🔌 Multi-Cloud & Multi-Database Support
Connect to diverse data sources with unified configuration:
- **Cloud Platforms:** Azure (Data Explorer/Kusto), AWS (Athena, RDS), GCP (BigQuery)
- **Databases:** PostgreSQL, MySQL, SQL Server, SQLite (any SQLAlchemy-compatible database)
- **APIs:** REST endpoints with flexible authentication
- **Files:** Local CSV files for static data

### 🔐 Smart Credential Management
Define credentials once, reuse across multiple data sources:
- Cloud-native authentication (Azure Default Credentials, AWS IAM, GCP Service Accounts)
- Environment variable substitution keeps secrets out of config files
- Support for access keys, service principals, connection strings, and bearer tokens

### ⚡ Asynchronous Execution
Reports execute efficiently with:
- Concurrent query execution across multiple data sources
- Configurable timeouts and retry logic with exponential backoff
- Non-blocking I/O for fast report generation

### 🎨 Rich Visualizations
Create professional reports with:
- **Data Tables** with automatic formatting
- **Interactive Charts** (bar, line, scatter) powered by Plotly
- **KPI Cards** with gradient styling
- **Progress Bars** and completion meters
- **Alert Boxes** with conditional formatting
- **Custom HTML** with full Jinja2 templating

### 📧 Reliable Email Delivery
- SMTP delivery with TLS/STARTTLS support
- Configurable from/to addresses with template variables
- Email-client compatible HTML (tested with Gmail, Outlook, Apple Mail)
- Preview reports in browser before sending

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras

# Set up environment variables (optional for examples)
export POSTGRES_USER=reporter
export POSTGRES_PASSWORD=reportpw
export CSV_ROOT="$(pwd)/tests/fixtures/data"

# Run the sample report (preview only, no email)
queryhub run-report config/reports/daily_sales_report --no-email --output-html report.html

# Open the generated report
open report.html  # macOS
# or: xdg-open report.html  # Linux
# or: start report.html  # Windows
```

## 📊 Live Examples

See QueryHub in action with these real HTML reports generated from our test suite:

### 📈 Sales Dashboard Report
A complete business intelligence dashboard featuring:
- **KPI Cards** – Key metrics with gradient styling (Total Revenue: $2.5M, Average Order: $845)
- **Data Tables** – Sales by region with formatted numbers
- **Interactive Charts** – Revenue trends, transaction counts, and correlations
- **Progress Bars** – Goal completion with percentage indicators
- **Ranked Lists** – Top performers with medal rankings 🥇🥈🥉
- **Alert Boxes** – Conditional warnings based on data thresholds
- **Status Badges** – Product/category indicators with color coding

**[📄 View Sales Dashboard Report →](docs/images/sales_dashboard_report.html)**

### 🎨 All Visualizations Report
Complete showcase of every QueryHub component type:
- Simple and aggregated data tables
- Text components with custom formatting
- Custom HTML layouts and cards
- List and badge components
- Conditional formatting examples

**[📄 View All Visualizations Report →](docs/images/all_visualizations_report.html)**

### 📉 Chart Visualizations Report
Data visualization focus with Plotly charts:
- **Bar Charts** – Regional revenue comparison, product performance
- **Line Charts** – Time-series revenue trends, transaction counts over time  
- **Scatter Plots** – Multi-dimensional analysis (units vs revenue, system health metrics)
- **Color Grouping** – Category-based coloring for better insights
- **Summary Stats** – Aggregated statistics table

**[📄 View Chart Visualizations Report →](docs/images/chart_visualizations_report.html)**

### Generate These Examples Locally

```bash
# Run integration tests to generate all example reports
make test-all

# View generated HTML reports
open test_output/sales_dashboard_report.html
open test_output/all_visualizations_report.html
open test_output/chart_visualizations_report.html

# View email versions (.eml files) in your email client
open test_output/all_visualizations_email.eml
```

For more visualization examples and styling options, see [HTML Visualizations Reference](docs/reference/html-visualizations.md).

## ⚙️ Configuration

QueryHub uses a folder-based configuration structure for better organization and maintainability:

```
config/
 ├─ smtp/                            # SMTP configurations
 │   ├─ default.yaml                # Default SMTP settings
 │   └─ production.yaml             # Optional: production SMTP
 ├─ templates/                       # Jinja2 HTML templates
 │   └─ report.html.j2              # Default report template
 ├─ providers/                       # Data source configurations
 │   ├─ credentials.yaml            # Shared credentials
 │   ├─ 01_databases.yaml           # Database providers
 │   ├─ 02_azure.yaml               # Azure providers
 │   └─ 03_rest_apis.yaml           # REST API providers
 └─ reports/                         # Report definitions
     └─ daily_sales_report/         # Each report in its own folder
         ├─ metadata.yaml           # Report metadata
         ├─ 01_component.yaml       # Component 1 (ordered by prefix)
         └─ 02_component.yaml       # Component 2
```

### SMTP Configuration

Define your email delivery settings in `config/smtp/default.yaml`:

```yaml
host: smtp.gmail.com
port: 587
use_tls: false
starttls: true
timeout_seconds: 30
username: ${SMTP_USERNAME:reporter@example.com}
password: ${SMTP_PASSWORD}
default_from: reports@example.com
default_to:
  - team@example.com
subject_template: "{{ title }} – {{ generated_at.strftime('%Y-%m-%d') }}"
```

Environment variables like `${SMTP_PASSWORD}` keep secrets out of version control.

**Per-Report SMTP Configuration:** You can specify a different SMTP configuration in your report's metadata:

```yaml
# config/reports/my_report/metadata.yaml
id: my_report
title: My Report
smtp_config: production.yaml  # Uses config/smtp/production.yaml
```

**HTML-Only Mode:** If no SMTP configuration exists and `--no-email` is used, QueryHub operates in HTML-only mode.

### Credentials & Providers

Credentials and providers can be split across multiple files for better organization. All YAML files in the `providers/` directory are automatically merged:

```yaml
# config/providers/credentials.yaml - Define credentials once
credentials:
  - id: azure_default
    azure:
      type: default_credentials  # Uses Azure CLI, Managed Identity, or environment
  
  - id: postgres_creds
    postgresql:
      type: username_password
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
  
  - id: api_token
    generic:
      type: token
      token: ${API_TOKEN}
      header_name: Authorization
      template: "Bearer {token}"

# config/providers/01_databases.yaml - Database providers
providers:
  - id: reporting_db
    resource:
      sql:
        dsn: postgresql+asyncpg://localhost:5432/reports
    credentials: postgres_creds

# config/providers/02_azure.yaml - Azure providers
providers:
  - id: azure_kusto
    resource:
      adx:
        cluster_uri: https://help.kusto.windows.net
        database: Samples
        default_timeout_seconds: 60
    credentials: azure_default

# config/providers/03_rest_apis.yaml - REST API providers
providers:
  - id: weather_api
    resource:
      rest:
        base_url: https://api.openweathermap.org/data/2.5/
    credentials: api_token
```

**Supported Cloud Providers:**
- **Azure:** Default credentials, Managed Identity, Service Principal, Token
- **AWS:** Default credentials (boto3 chain), Access Key, IAM Role
- **GCP:** Default credentials (Application Default), Service Account
- **Generic:** Username/Password, Token, Connection String, No Authentication

For detailed credential configuration, see [Getting Started Guide](docs/guides/getting-started.md).

### Report Definition

Reports are now folder-based for better organization and maintainability. Each report has its own folder with metadata and component files:

```yaml
# config/reports/daily_sales_report/metadata.yaml
id: daily_sales_report
title: Daily Sales Report
description: Daily sales performance analytics

# Template filename (looks in config/templates/)
template: report.html.j2

# Optional: override default folders (relative or absolute paths)
# template_folder: ../../../custom_templates
# providers_folder: ../../../custom_providers
# smtp_config: production.yaml  # Use specific SMTP config from config/smtp/

# Email overrides (optional)
email:
  to:
    - sales-team@example.com
  subject_template: "Daily Sales Report – {{ generated_at.strftime('%B %d, %Y') }}"

# Scheduling (optional)
schedule:
  cron: "0 8 * * 1-5"  # Weekdays at 8 AM
  timezone: America/New_York
  enabled: true
```

Components are defined in separate files, numbered for ordering:

```yaml
# config/reports/daily_sales_report/01_total_revenue.yaml
id: total_revenue
title: Total Revenue Today
provider: reporting_db

query:
  text: |
    SELECT SUM(revenue) as total FROM sales WHERE date = CURRENT_DATE

render:
  type: text
  options:
    template: "Total Revenue: ${value:,.2f}"
    value_path: total

# config/reports/daily_sales_report/02_sales_by_region.yaml
id: sales_by_region
title: Sales by Region
provider: reporting_db

query:
  text: |
    SELECT region, SUM(revenue) as total_revenue, COUNT(*) as orders
    FROM sales
    WHERE date = CURRENT_DATE
    GROUP BY region
    ORDER BY total_revenue DESC

render:
  type: table
  options:
    columns: [region, total_revenue, orders]

# config/reports/daily_sales_report/03_revenue_trend.yaml
id: revenue_trend
title: 30-Day Revenue Trend
provider: reporting_db

query:
  text: |
    SELECT date, SUM(revenue) as revenue
    FROM sales
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY date
    ORDER BY date

render:
  type: chart
  options:
    chart_type: line
    x_field: date
    y_field: revenue
    title: "30-Day Revenue Trend"
```

## 🔧 Command Line Interface

QueryHub provides a simple CLI for running and managing reports:

### Run a Report

```bash
# Run report from folder and send via email
queryhub run-report config/reports/daily_sales_report

# Preview report without sending email
queryhub run-report config/reports/daily_sales_report --no-email

# Save report to HTML file
queryhub run-report config/reports/daily_sales_report --output-html report.html --no-email

# Enable verbose logging
queryhub run-report config/reports/daily_sales_report -v
```

**Note:** All configuration is in the report's metadata.yaml and config folder structure. Templates, providers, and SMTP settings are auto-discovered.

### List Available Reports

```bash
queryhub list-reports config
```

For more CLI options, see [CLI Reference](docs/reference/cli.md).

## 🧩 Extending QueryHub

### Adding Custom Providers

QueryHub makes it easy to add support for new data sources. Implement the `QueryProvider` interface:

```python
from typing import Any, Mapping
from queryhub.providers.base import QueryProvider, QueryResult
from queryhub.core.errors import ProviderExecutionError

class ElasticsearchProvider(QueryProvider):
    """Execute queries against Elasticsearch."""
    
    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute an Elasticsearch query."""
        index = query.get("index")
        body = query.get("body")
        
        if not index or not body:
            raise ProviderExecutionError("Elasticsearch requires 'index' and 'body'")
        
        # Execute your query
        response = await self._client.search(index=index, body=body)
        
        return QueryResult(
            data=response["hits"]["hits"],
            metadata={"total": response["hits"]["total"]["value"]}
        )
    
    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()
```

Register your custom provider:

```python
from pathlib import Path
from queryhub.config.models import ProviderType
from queryhub.core.providers import build_default_provider_registry
from queryhub.services import QueryHubApplicationBuilder

# Register custom provider
registry = build_default_provider_registry()
registry.register(ProviderType("elasticsearch"), ElasticsearchProvider)

# Build application with custom registry
builder = QueryHubApplicationBuilder(
    config_dir=Path("config"),
    templates_dir=Path("templates"),
)
executor = await builder.create_executor()
```

For a complete guide on implementing custom providers, see existing providers in `src/queryhub/providers/`.

### Programmatic Usage

Use QueryHub as a library in your Python applications:

```python
from pathlib import Path
from queryhub.services import QueryHubApplicationBuilder

# Build the application
builder = QueryHubApplicationBuilder(
    config_dir=Path("config"),
    templates_dir=Path("templates"),
    auto_reload_templates=True,  # Enable for development
)

# Create report executor
executor = await builder.create_executor()

# Execute a report
result = await executor.execute_report("daily_sales")

print(f"Report generated: {result.html_path}")
print(f"Email sent: {result.email_sent}")
```

Override any component by passing custom implementations that satisfy the contracts in `queryhub.core.contracts`.

## 🧪 Testing & Development

QueryHub includes comprehensive testing and code quality tools:

### Run Tests

```bash
# Run unit tests only
make test-unit
# or: pytest tests/ -v -m "not integration"

# Run all tests including integration tests
make test-all
# or: pytest tests/ -v

# Run with coverage
pytest --cov=queryhub --cov-report=html tests/
```

### Code Quality

```bash
# Run all quality checks (linting + type checking + security)
make check

# Individual checks
make lint          # Ruff linter
make typecheck     # mypy type checking
make security      # Bandit security analysis
make safety-check  # Dependency vulnerability scanning
```

Or run tools directly:

```bash
ruff check src/ tests/
mypy src/
bandit -r src/ -c .bandit
safety check
```

### Installing Development Dependencies

```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Or install only dev extras
uv sync --extra dev
```

For more development commands, see [uv Commands Reference](docs/reference/uv-commands.md).

## 📚 Documentation

- **[Getting Started](docs/guides/getting-started.md)** – Step-by-step tutorial from installation to first report
- **[Installation Guide](docs/guides/installation.md)** – Detailed installation and environment setup
- **[HTML Visualizations](docs/reference/html-visualizations.md)** – Complete guide to all visualization types
- **[CLI Reference](docs/reference/cli.md)** – Command-line interface documentation
- **[Azure Credentials](docs/guides/azure-default-credentials.md)** – Azure authentication configuration
- **[Email Testing](docs/guides/email-testing.md)** – Testing email delivery locally
- **[Security Tools](docs/reference/security-tools.md)** – Security scanning with Bandit and Safety

## 🤝 Contributing

Contributions are welcome! Please see:
- **[CONTRIBUTING.md](CONTRIBUTING.md)** – Contribution guidelines
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** – Community standards

For questions or support, contact: **idevhub@proton.me**

## 📝 License

QueryHub is released under the [MIT License](LICENSE).

## 🙏 Acknowledgments

QueryHub is built with these excellent open-source projects:
- **[uv](https://github.com/astral-sh/uv)** – Fast Python package manager
- **[Plotly](https://plotly.com/python/)** – Interactive visualization library
- **[SQLAlchemy](https://www.sqlalchemy.org/)** – SQL toolkit and ORM
- **[Jinja2](https://jinja.palletsprojects.com/)** – Template engine
- **[Azure SDK](https://github.com/Azure/azure-sdk-for-python)** – Azure cloud integration
- **[boto3](https://github.com/boto/boto3)** – AWS SDK for Python
- **[Google Cloud SDK](https://github.com/googleapis/google-cloud-python)** – GCP integration

---

**Made with ❤️ by the QueryHub team**

# QueryHub

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

QueryHub turns declarative YAML configuration into automated, fully rendered HTML email reports. It fans out asynchronous queries to heterogeneous data sources, binds the responses to Jinja2 templates, and delivers the resulting document via SMTP.

## Highlights
- **Multi-cloud ready** – Unified architecture supporting Azure, AWS, and GCP with reusable credential entities
- **Config-first** – Providers, credentials, report layout, and SMTP definitions live in YAML with environment-variable overrides (`${VAR:default}`) for secrets
- **Credential reusability** – Define credentials once, reference them across multiple providers by ID
- **Pluggable data providers** – Built-in adapters for Azure Data Explorer (Kusto), SQL (SQLAlchemy async engines), REST APIs (aiohttp), and local CSV files. New providers implement `BaseQueryProvider`
- **Async execution** – Components run concurrently with configurable timeouts, retries, and exponential backoff
- **Templateable HTML** – Reports are rendered with Jinja2 templates; components (tables, charts, text) compose the final document
- **Email delivery** – Uses SMTP (via `aiosmtplib`) with TLS/STARTTLS, multiple credential options, and a DKIM stub hook
- **SOLID architecture** – Clean separation of concerns with dependency injection and interface-based design
- **CI-ready** – Packaging via `pyproject.toml`, linting with Ruff, typing with mypy, tests with pytest/pytest-asyncio, and a GitHub Actions workflow

## Quick start
```bash
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras

# Optional: export secrets used in example YAML
export POSTGRES_USER=reporter
export POSTGRES_PASSWORD=reportpw
export CSV_ROOT="$(pwd)/tests/fixtures/data"

# Run a sample report without sending email
queryhub run-report sample_report --config-dir config --templates-dir templates --no-email
```

> **Tip:** `queryhub run-report sample_report --no-email --output-html report.html` writes the rendered HTML without sending email.

## Email Report Examples

QueryHub generates fully-styled HTML email reports with multiple visualization types. Here are live examples from our test reports:

### Sales Dashboard Report
A comprehensive business intelligence report featuring:
- 📊 **Interactive Charts** - Bar charts, line graphs, scatter plots with Plotly
- 📋 **Data Tables** - Formatted tables with sortable columns
- 💹 **KPI Cards** - Key metrics with gradient backgrounds and trend indicators
- 📈 **Progress Bars** - Visual progress indicators with percentage completion
- 🏆 **Ranked Lists** - Top performers with medal indicators (🥇🥈🥉)
- ⚠️ **Alert Boxes** - Conditional styling based on data thresholds
- 🎯 **Product Badges** - Status indicators with color coding

**[📄 View Sales Dashboard Report →](docs/images/sales_dashboard_report.html)**

### All Visualizations Report
Comprehensive showcase of all available component types:
- Tables (simple and aggregated)
- Charts (bar, line, scatter)
- Text components with templating
- Custom HTML components
- Conditional formatting

**[📄 View All Visualizations Report →](docs/images/all_visualizations_report.html)**

### Chart Visualizations Report
Focus on data visualization with various chart types:
- Revenue trends over time (line charts)
- Regional comparisons (bar charts)
- Correlation analysis (scatter plots)
- Multi-dimensional data with color grouping

**[📄 View Chart Visualizations Report →](docs/images/chart_visualizations_report.html)**

**To generate these examples yourself:**
```bash
# Run all integration tests to generate report examples
make test-all

# View generated reports in test_output/
open test_output/all_visualizations_report.html
open test_output/sales_dashboard_report.html
open test_output/chart_visualizations_report.html

# Open email versions (.eml files) in your email client
open test_output/all_visualizations_email.eml
```

## Configuration model
```
config/
 ├─ smtp.yaml            # SMTP defaults (host, TLS, credentials, subject template)
 ├─ providers/
 │   └─ providers.yaml   # Provider definitions (ADX/SQL/REST/CSV)
 └─ reports/
     └─ sample_report.yaml
```

### SMTP (`config/smtp.yaml`)
```yaml
host: smtp.example.com
port: 587
use_tls: false
starttls: true
timeout_seconds: 30
username: ${SMTP_USERNAME:reporter}
password: ${SMTP_PASSWORD:changeme}
default_from: reports@example.com
default_to:
  - data-team@example.com
subject_template: "{{ title }} – {{ generated_at.strftime('%Y-%m-%d') }}"
```

### Provider definition (`config/providers/providers.yaml`)

The new architecture separates credentials from providers for reusability:

```yaml
# Define credentials once, organized by cloud provider
credentials:
  - id: azure_default_credentials
    azure:
      type: default_credentials
  
  - id: postgres_credentials
    postgresql:
      type: username_password
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
  
  - id: rest_api_token
    generic:
      type: token
      token: ${API_TOKEN}
      header_name: Authorization
      template: "Bearer {token}"

# Providers reference credentials by ID
providers:
  - id: adx_marketing
    resource:
      adx:
        cluster_uri: https://help.kusto.windows.net
        database: Samples
        default_timeout_seconds: 60
    credentials: azure_default_credentials
  
  - id: postgres_reporting
    resource:
      sql:
        dsn: postgresql+asyncpg://${POSTGRES_HOST}:${POSTGRES_PORT}/reporting
    credentials: postgres_credentials
  
  - id: rest_weather
    resource:
      rest:
        base_url: https://api.open-meteo.com/v1/
    credentials: rest_api_token
```

**Supported Cloud Providers:**
- **Azure**: Default credentials, Managed Identity, Service Principal, Token
- **AWS**: Default credentials, Access Key, IAM Role
- **GCP**: Default credentials, Service Account
- **Generic**: Username/Password, Token, Connection String, No credential

See [Multi-Cloud Architecture](docs/reference/new-architecture.md) for detailed information.

### Report definition (`config/reports/sample_report.yaml`)
Each component binds to a provider and declares how to render the response.
```yaml
components:
  - id: revenue_snapshot
    provider: postgres_reporting
    query:
      text: |
        SELECT country, total_revenue FROM finance.revenue_summary
    render:
      type: table
      options:
        columns: [country, total_revenue]
  - id: pipeline_chart
    provider: csv_local
    query:
      path: pipeline.csv
    render:
      type: chart
      options:
        chart_type: bar
        x_field: stage
        y_field: amount
```

## CLI
```
queryhub run-report <report_id> \
  --config-dir config \
  --templates-dir templates \
  [--output-html out.html] \
  [--no-email] \
  [-v]

queryhub list-reports --config-dir config
```

## Application composition & DI

QueryHub follows **100% SOLID principles** and clean architecture patterns. The codebase features:

- ✅ **Single Responsibility** - Each class has one clear purpose
- ✅ **Open/Closed** - Extensible without modifying existing code
- ✅ **Liskov Substitution** - Implementations are properly substitutable
- ✅ **Interface Segregation** - Minimal, focused protocols
- ✅ **Dependency Inversion** - High-level modules depend on abstractions

Library consumers can build the orchestration stack programmatically via `QueryHubApplicationBuilder` which wires the config loader, provider factory, renderer registry, template engine, and email sender behind SOLID-friendly interfaces:

```python
from pathlib import Path
from queryhub.services import QueryHubApplicationBuilder

builder = QueryHubApplicationBuilder(
  config_dir=Path("config"),
  templates_dir=Path("templates"),
  auto_reload_templates=True,
)
executor = await builder.create_executor()
result = await executor.execute_report("sample_report")
```

Override any dependency (provider factory, renderer resolver, template engine, email sender) by passing custom implementations that satisfy the contracts in `queryhub.core.contracts`.

**Architecture Documentation:**
- [SOLID Architecture Guide](docs/reference/solid-architecture.md) - Detailed design patterns and principles
- [Refactoring Summary](docs/reference/refactoring-summary.md) - Complete list of improvements
- [Migration Guide](docs/guides/migration.md) - How to update your code

## Extending providers
Subclass `QueryProvider`, implement `execute()`, and register it with a `ProviderRegistry` instance before building the application:

```python
from pathlib import Path

from queryhub.config import ConfigLoader
from queryhub.config.models import ProviderType
from queryhub.core.providers import DefaultProviderFactory, build_default_provider_registry
from my_project.providers import MyAPIProvider

loader = ConfigLoader(Path("config"))
settings = await loader.load()
registry = build_default_provider_registry()
registry.register(ProviderType("myapi"), MyAPIProvider)
factory = DefaultProviderFactory(settings.providers, registry)
```

Providers receive the parsed query dictionary from YAML and should return a `QueryResult`. Custom registries can then be injected via `QueryHubApplicationBuilder`.

## How to add a new provider

Adding a custom provider to QueryHub involves three main steps: creating the provider class, defining the configuration model, and registering the provider.

### Step 1: Create your provider class

Subclass `QueryProvider` and implement the `execute()` method:

```python
# my_project/providers/elasticsearch.py
from typing import Any, Mapping
from queryhub.providers.base import QueryProvider, QueryResult
from queryhub.config.models import BaseProviderConfig
from queryhub.core.errors import ProviderExecutionError

class ElasticsearchProvider(QueryProvider):
    """Execute queries against Elasticsearch."""

    def __init__(self, config: BaseProviderConfig) -> None:
        super().__init__(config)
        # Initialize your client here
        self._client = None  # Initialize with config parameters

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute an Elasticsearch query."""
        # Extract query parameters
        index = query.get("index")
        body = query.get("body")
        
        if not index or not body:
            raise ProviderExecutionError("Elasticsearch queries require 'index' and 'body'")
        
        # Execute your query
        # response = await self._client.search(index=index, body=body)
        response = {"hits": []}  # Example response
        
        # Return normalized result
        return QueryResult(
            data=response.get("hits", []),
            metadata={"total": len(response.get("hits", []))}
        )

    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()
```

### Step 2: Define configuration model (optional)

For type-safe configuration, create a config model:

```python
# my_project/config.py
from dataclasses import dataclass
from queryhub.config.models import BaseProviderConfig

@dataclass
class ElasticsearchProviderConfig(BaseProviderConfig):
    """Configuration for Elasticsearch provider."""
    hosts: list[str]
    timeout: int = 30
```

### Step 3: Register your provider

Register the provider with the registry before building your application:

```python
from pathlib import Path
from queryhub.config.models import ProviderType
from queryhub.core.providers import build_default_provider_registry
from queryhub.services import QueryHubApplicationBuilder
from my_project.providers.elasticsearch import ElasticsearchProvider

# Build registry with your custom provider
registry = build_default_provider_registry()
registry.register(ProviderType("elasticsearch"), ElasticsearchProvider)

# Create application with custom registry
builder = QueryHubApplicationBuilder(
    config_dir=Path("config"),
    templates_dir=Path("templates"),
)
# Inject custom registry by providing a custom provider factory
# Or use the builder's provider_factory parameter if available
```

### Step 4: Configure your provider in YAML

Add your provider definition to `config/providers/providers.yaml`:

```yaml
providers:
  - id: my_elasticsearch
    type: elasticsearch
    target:
      hosts:
        - https://es.example.com:9200
    credentials:
      type: bearer_token
      token: ${ES_TOKEN}
```

### Step 5: Use in reports

Reference your provider in report configurations:

```yaml
# config/reports/my_report.yaml
components:
  - id: search_results
    provider: my_elasticsearch
    query:
      index: products
      body:
        query:
          match_all: {}
    render:
      type: table
      options:
        columns: [name, price, category]
```

### Provider best practices

- **Handle missing dependencies gracefully**: Use `_raise_missing_dependency()` for optional packages
- **Validate configuration**: Override `_validate_config()` to check required settings
- **Return normalized data**: Always return `QueryResult` with consistent data structures
- **Implement cleanup**: Override `close()` to release connections and resources
- **Add metadata**: Include useful metadata (row counts, execution time) in results
- **Handle errors**: Raise `ProviderExecutionError` with descriptive messages

See existing providers (`src/queryhub/providers/`) for complete implementation examples.

## Templates
- Default template lives in `templates/report.html.j2` and includes styling plus Plotly support.
- Add custom templates beside it and reference them by filename in report configs (`template: my-report.html.j2`).

## Testing & linting
```bash
ruff check
mypy src
bandit -r src/ -c .bandit  # Security linting
safety check                # Dependency vulnerability scanning
pytest --asyncio-mode=auto
```

Or use the Makefile for convenience:
```bash
make install       # Install with uv
make lint          # Run Ruff linter
make typecheck     # Run mypy type checking
make security      # Run Bandit security checks
make safety-check  # Check for vulnerable dependencies
make check         # Run all checks (lint + typecheck + security)
make test-unit     # Run unit tests only
make test-all      # Run all tests including integration
```

**Note:** QueryHub uses [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management.

Example configs for tests live under `tests/fixtures/` and rely on environment placeholders (set `CSV_ROOT` to run the integration test).

## Additional resources
- `docs/` – extended guides and CLI reference.
- `docs/guides/uv-migration.md` – migration guide from pip to uv.
- `docs/reference/security-tools.md` – security scanning with Bandit and Safety.
- `examples/` – sample YAML snippets.
- `scripts/setup_env.sh` – helper for local virtualenv bootstrap.

## Contributing & license
Contributions are welcome! See `CONTRIBUTING.md` and the project `CODE_OF_CONDUCT.md`. QueryHub is released under the MIT License (`LICENSE`).

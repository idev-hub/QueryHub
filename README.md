# QueryHub

QueryHub turns declarative YAML configuration into automated, fully rendered HTML email reports. It fans out asynchronous queries to heterogeneous data sources, binds the responses to Jinja2 templates, and delivers the resulting document via SMTP.

## Highlights
- **Config-first** – Providers, credentials, report layout, and SMTP definitions live in YAML with environment-variable overrides (`${VAR:default}`) for secrets.
- **Pluggable data providers** – Built-in adapters for Azure Data Explorer (Kusto), SQL (SQLAlchemy async engines), REST APIs (aiohttp), and local CSV files. New providers subclass `QueryProvider`.
- **Async execution** – Components run concurrently with configurable timeouts, retries, and exponential backoff.
- **Templateable HTML** – Reports are rendered with Jinja2 templates; components (tables, charts, text) compose the final document.
- **Email delivery** – Uses SMTP (via `aiosmtplib`) with TLS/STARTTLS, multiple credential options, and a DKIM stub hook.
- **CI-ready** – Packaging via `pyproject.toml`, linting with Ruff, typing with mypy, tests with pytest/pytest-asyncio, and a GitHub Actions workflow.

## Quick start
```bash
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Optional: export secrets used in example YAML
export POSTGRES_USER=reporter
export POSTGRES_PASSWORD=reportpw
export CSV_ROOT="$(pwd)/tests/fixtures/data"

# Run a sample report without sending email
queryhub run-report sample_report --config-dir config --templates-dir templates --no-email
```

> **Tip:** `queryhub run-report sample_report --no-email --output-html report.html` writes the rendered HTML without sending email.

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
```yaml
providers:
  - id: postgres_reporting
    type: sql
    target:
      dsn: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db.internal/reporting
    credentials:
      type: username_password
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
```

ADX, REST, and CSV providers follow the same pattern, each supporting credential types such as managed identity, service principal, username/password, connection string, bearer token, or none.

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

## Extending providers
Subclass `QueryProvider`, implement `execute()`, and register it in `ProviderFactory._registry`. Providers receive the parsed query dictionary from YAML and should return a `QueryResult`.

## Templates
- Default template lives in `templates/report.html.j2` and includes styling plus Plotly support.
- Add custom templates beside it and reference them by filename in report configs (`template: my-report.html.j2`).

## Testing & linting
```bash
ruff check
mypy src
pytest --asyncio-mode=auto
```

Example configs for tests live under `tests/fixtures/` and rely on environment placeholders (set `CSV_ROOT` to run the integration test).

## Additional resources
- `docs/` – extended guides and CLI reference.
- `examples/` – sample YAML snippets.
- `scripts/setup_env.sh` – helper for local virtualenv bootstrap.

## Contributing & license
Contributions are welcome! See `CONTRIBUTING.md` and the project `CODE_OF_CONDUCT.md`. QueryHub is released under the MIT License (`LICENSE`).

# Getting Started

Welcome to QueryHub! This walkthrough shows how to install the project locally, configure data providers, render a report, and send it via email.

## 1. Install dependencies
```bash
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras
```

## 2. Review the configuration structure

QueryHub uses a folder-based configuration. See the complete working example in [`config/`](../../config/):

**SMTP Settings:** [`config/smtp/default.yaml`](../../config/smtp/default.yaml)
- Email server configuration
- Supports environment variables for credentials

**Data Providers:** [`config/providers/`](../../config/providers/)
- `credentials.yaml` - Authentication credentials
- `01_databases.yaml` - Database connections
- `02_azure.yaml` - Azure Data Explorer
- Files automatically merged

**Templates:** [`config/templates/`](../../config/templates/)
- `report.html.j2` - Default HTML template
- Jinja2 templating engine

**Reports:** [`config/reports/`](../../config/reports/)
- Each report is a folder (e.g., `daily_sales_report/`)
- `metadata.yaml` - Report settings
- `01_*.yaml`, `02_*.yaml` - Components (merged in order)

Environment variables can override secrets via `${VAR:default}` placeholders.

## 3. Configure a provider

See complete examples in [`config/providers/`](../../config/providers/).

Add to `config/providers/credentials.yaml`:
```yaml
credentials:
  - id: postgres_creds
    postgresql:
      type: username_password
      username: ${PG_USER}
      password: ${PG_PASSWORD}
```

Add to `config/providers/01_databases.yaml`:
```yaml
providers:
  - id: customers_pg
    resource:
      sql:
        dsn: postgresql+asyncpg://${PG_HOST:localhost}:5432/customers
    credentials: postgres_creds
    default_timeout_seconds: 45
```

All `*.yaml` files in `config/providers/` are automatically merged.

## 4. Author a report

See the complete example in [`config/reports/daily_sales_report/`](../../config/reports/daily_sales_report/).

Create a folder-based report in `config/reports/customers_daily/`:

**metadata.yaml:**
```yaml
id: customers_daily
title: Daily Customer Metrics
template: report.html.j2
email:
  to:
    - analytics@example.com
```

**01_customer_table.yaml:**
```yaml
id: customer_table
provider: customers_pg
query:
  text: |
    SELECT plan, COUNT(*) AS subscribers
    FROM subscriptions
    WHERE active = true
    GROUP BY plan
render:
  type: table
```

**02_churn_text.yaml:**
```yaml
id: churn_text
provider: customers_pg
query:
  text: |
    SELECT churn_rate
    FROM metrics.daily_summary
    ORDER BY observed_at DESC
    LIMIT 1
render:
  type: text
  options:
    template: "Churn rate (24h): {value:.2%}"
    value_path: 0.churn_rate
```

Components are automatically merged in numeric order (01_, 02_, etc.).

## 5. Render the report
```bash
queryhub run-report config/reports/customers_daily --output-html customers.html --no-email
```

Open `customers.html` in a browser to preview the layout.

For all command options, see [CLI Reference](../reference/cli.md).

## 6. Send the email
Update `config/smtp/default.yaml` with your SMTP host and credentials (or export `SMTP_USERNAME`, `SMTP_PASSWORD`, etc.). Then run:
```bash
queryhub run-report config/reports/customers_daily
```

QueryHub will execute the report, render the HTML, and deliver it using the SMTP settings.

## Next steps
- Add scheduling metadata (`schedule.cron`) to reports for external schedulers.
- Implement additional providers by subclassing `queryhub.providers.base.QueryProvider`.
- Embed QueryHub in another service with `QueryHubApplicationBuilder` to plug custom factories or template engines.
- Explore the CLI reference for more commands and flags.

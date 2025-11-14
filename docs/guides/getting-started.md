# Getting Started

Welcome to QueryHub! This walkthrough shows how to install the project locally, configure data providers, render a report, and send it via email.

## 1. Install dependencies
```bash
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. Review the configuration tree
```
config/
 ├─ smtp.yaml            # SMTP defaults
 ├─ providers/           # Provider definitions
 └─ reports/             # Report layouts and email overrides
templates/               # Jinja2 templates
```

Environment variables can override secrets via `${VAR:default}` placeholders. For example, set `POSTGRES_PASSWORD` to keep database credentials out of YAML.

## 3. Configure a provider
Add a new entry to `config/providers/providers.yaml`:
```yaml
- id: customers_pg
	type: sql
	target:
		dsn: postgresql+asyncpg://${PG_USER}:${PG_PASSWORD}@${PG_HOST:localhost}:5432/customers
	credentials:
		type: username_password
		username: ${PG_USER}
		password: ${PG_PASSWORD}
	default_timeout_seconds: 45
```

## 4. Author a report
Create `config/reports/customers.yaml`:
```yaml
id: customers_daily
title: Daily Customer Metrics
template: report.html.j2
components:
	- id: customer_table
		provider: customers_pg
		query:
			text: |
				SELECT plan, COUNT(*) AS subscribers
				FROM subscriptions
				WHERE active = true
				GROUP BY plan
		render:
			type: table
	- id: churn_text
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
email:
	to:
		- analytics@example.com
```

## 5. Render the report
```bash
queryhub run-report customers_daily --config-dir config --templates-dir templates --output-html customers.html --no-email
```

Open `customers.html` in a browser to preview the layout.

## 6. Send the email
Update `config/smtp.yaml` with your SMTP host and credentials (or export `SMTP_USERNAME`, `SMTP_PASSWORD`, etc.). Then run:
```bash
queryhub run-report customers_daily --config-dir config --templates-dir templates
```

QueryHub will execute the report, render the HTML, and deliver it using the SMTP settings.

## Next steps
- Add scheduling metadata (`schedule.cron`) to reports for external schedulers.
- Implement additional providers by subclassing `queryhub.providers.base.QueryProvider`.
- Embed QueryHub in another service with `QueryHubApplicationBuilder` to plug custom factories or template engines.
- Explore the CLI reference for more commands and flags.

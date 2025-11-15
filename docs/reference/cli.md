# CLI Reference

QueryHub provides a simple command-line interface for running and managing reports.

## `run-report`

Execute a report from its folder path.

```bash
queryhub run-report REPORT_FOLDER \
  [--output-html FILE] \
  [--email / --no-email] \
  [--verbose]
```

| Option | Description |
| --- | --- |
| `REPORT_FOLDER` | Required. Path to report folder (e.g., `config/reports/my_report`) |
| `--output-html` | Path to write the rendered HTML file. |
| `--email / --no-email` | Toggle sending via email. Default: email enabled. |
| `--verbose` / `-v` | Enable debug logging. |

**How it works:**
- Auto-discovers config structure from report folder path
- Templates loaded from `config/templates/` (or override in metadata)
- Providers loaded from `config/providers/` (or override in metadata)
- SMTP config loaded from `config/smtp/default.yaml` (or override in metadata)

**Examples:**
```bash
# Run report and send email
queryhub run-report config/reports/daily_sales

# Preview only (no email)
queryhub run-report config/reports/daily_sales --no-email

# Save to file
queryhub run-report config/reports/daily_sales --output-html report.html --no-email

# Verbose logging
queryhub run-report config/reports/daily_sales -v
```

## `list-reports`

List all available reports in a config directory.

```bash
queryhub list-reports CONFIG_DIR
```

| Option | Description |
| --- | --- |
| `CONFIG_DIR` | Required. Path to config directory (e.g., `config`) |

**Example:**
```bash
queryhub list-reports config
# Output:
# daily_sales_report    Daily Sales Performance Report
```

## Exit codes
| Code | Meaning |
| --- | --- |
| `0` | Command completed successfully. |
| `1` | Validation failure or unhandled error. |

## Environment variables
- `CSV_ROOT`, `POSTGRES_USER`, etc. supply values for `${VAR}` placeholders in YAML.

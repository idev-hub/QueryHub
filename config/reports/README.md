# QueryHub Reports Configuration

This directory contains folder-based report configurations. Each report is a separate folder containing:

## Report Folder Structure

```
reports/
  daily_sales_report/           # Report folder (one per report)
    metadata.yaml               # Report metadata and configuration
    01_total_revenue.yaml       # Component 1 (numbered for ordering)
    02_revenue_by_category.yaml # Component 2
    03_sales_trend.yaml         # Component 3
    ...                         # Additional components
```

## Metadata File (`metadata.yaml`)

Contains report-level configuration:

```yaml
id: report_id
title: Report Title
description: Report description

# Template path (relative to templates/ or absolute)
html_template_path: report.html.j2

# Optional: credentials folder path (relative or absolute)
# credentials_config_folder: ../../providers

# Email configuration
email:
  to: [email@example.com]
  subject_template: "Report - {{ generated_at }}"

# Scheduling
schedule:
  cron: "0 8 * * *"
  timezone: UTC
  enabled: true
```

## Component Files

Component files are numbered for ordering (01_, 02_, etc.) and contain:

```yaml
id: component_id
title: Component Title
description: Component description
provider: provider_id

query:
  text: |
    SELECT * FROM table

render:
  type: table  # or chart, text, html
  options:
    # Render-specific options
```

## Running Reports

Execute a report using the CLI:

```bash
queryhub run-report config/reports/daily_sales_report
```

Everything (templates, providers, SMTP) is auto-discovered from the config structure.

# CLI Reference

QueryHub ships with a Typer-based CLI that exposes report execution and discovery commands. Install the package (`pip install -e .`) to make the `queryhub` command available.

## `run-report`
Execute a configured report, render the HTML output, and optionally send it via SMTP.

```
queryhub run-report REPORT_ID \
	--config-dir PATH \
	--templates-dir PATH \
	[--output-html FILE] \
	[--email / --no-email] \
	[--verbose]
```

| Option | Description |
| --- | --- |
| `REPORT_ID` | Required positional ID matching a YAML entry in `config/reports/`. |
| `--config-dir` | Root directory containing `smtp.yaml`, `providers/`, and `reports/`. Default: `config`. |
| `--templates-dir` | Directory with Jinja2 templates. Default: `templates`. |
| `--output-html` | Path to write the rendered HTML file. Disabled if omitted. |
| `--email / --no-email` | Toggle sending the result via SMTP. Enabled by default. |
| `--verbose` | Enables debug logging. |

Example:
```bash
queryhub run-report sample_report --config-dir config --templates-dir templates --output-html sample.html --no-email --verbose
```

## `list-reports`
Enumerate available report IDs and titles.

```
queryhub list-reports --config-dir PATH --templates-dir PATH
```

| Option | Description |
| --- | --- |
| `--config-dir` | Configuration root to scan. Default: `config`. |
| `--templates-dir` | Directory housing templates. Default: `templates`. |

Example:
```bash
queryhub list-reports --config-dir config
# sample_report    Executive Summary
# csv_only         CSV Fixture Report
```

## Exit codes
| Code | Meaning |
| --- | --- |
| `0` | Command completed successfully. |
| `1` | Validation failure or unhandled error. |

## Environment variables
- `CSV_ROOT`, `POSTGRES_USER`, etc. supply values for `${VAR}` placeholders in YAML.

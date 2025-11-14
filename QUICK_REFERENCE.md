# QueryHub Quick Reference Card

## 🚀 Building

```bash
# Quick build
./scripts/build_docker.sh

# Or with make
make build-dist

# Create archive
make build-archive

# Clean up
make clean-dist
```

## 📦 Distribution Structure

```
dist/
├── queryhub           # Executable (Linux/macOS)
├── queryhub.exe       # Executable (Windows)
├── queryhub.sh        # Unix wrapper
├── queryhub.bat       # Windows wrapper
├── templates/         # HTML templates
├── config/            # Configuration
└── examples/          # Usage examples
```

## ⚙️ Configuration Files

### SMTP (config/smtp.yaml)
```yaml
host: smtp.gmail.com
port: 587
username: ${SMTP_USERNAME}
password: ${SMTP_PASSWORD}
```

### Providers (config/providers/providers.yaml)
```yaml
providers:
  - id: my_db
    type: sql
    target:
      dsn: postgresql+asyncpg://user:pass@host/db
```

### Report (config/reports/my_report.yaml)
```yaml
id: my_report
title: My Report
components:
  - id: data
    provider: my_db
    query:
      text: SELECT * FROM table
    render:
      type: table
```

## 🎯 Common Commands

```bash
# List reports
./queryhub list-reports --config-dir config --templates-dir templates

# Run without email
./queryhub run-report REPORT_ID --no-email --output-html output.html

# Run with email
./queryhub run-report REPORT_ID

# Verbose mode
./queryhub run-report REPORT_ID -v

# Get help
./queryhub --help
./queryhub run-report --help
```

## 🔐 Environment Variables

```bash
# Linux/macOS
export SMTP_USERNAME="user@example.com"
export SMTP_PASSWORD="password"
export POSTGRES_USER="dbuser"
export POSTGRES_PASSWORD="dbpass"

# Windows (cmd)
set SMTP_USERNAME=user@example.com
set SMTP_PASSWORD=password

# Windows (PowerShell)
$env:SMTP_USERNAME="user@example.com"
$env:SMTP_PASSWORD="password"
```

## 📊 Visualization Types

### Table
```yaml
render:
  type: table
  options:
    columns: [col1, col2, col3]
```

### Chart
```yaml
render:
  type: chart
  options:
    chart_type: line  # bar, line, scatter, pie, area
    x_field: date
    y_field: value
```

### Text/Metric
```yaml
render:
  type: text
  options:
    template: "Total: {value}"
```

## 🔌 Provider Types

| Type | Example DSN/Config |
|------|-------------------|
| PostgreSQL | `postgresql+asyncpg://user:pass@host:5432/db` |
| MySQL | `mysql+aiomysql://user:pass@host:3306/db` |
| SQLite | `sqlite+aiosqlite:///./data/local.db` |
| SQL Server | `mssql+aioodbc://user:pass@host/db` |
| Azure Kusto | `cluster_uri: https://cluster.kusto.windows.net` |
| REST API | `base_url: https://api.example.com/v1/` |
| CSV | `root_path: ./data` |

### Azure Data Explorer Authentication

| Type | Use Case | Config |
|------|----------|--------|
| `default_credentials` | **Recommended** for local dev & Azure deployments | Auto-discovers credentials (Azure CLI, Managed Identity, etc.) |
| `managed_identity` | Azure resources with explicit client ID | Specify `client_id` if needed |
| `service_principal` | CI/CD pipelines & automation | Requires `client_id`, `client_secret`, `tenant_id` |

## 🔧 Troubleshooting

```bash
# Verify build environment
make verify-build

# Test distribution
make test-dist

# Verbose logging
./queryhub run-report REPORT_ID -v

# Check executable
file ./queryhub
./queryhub --help
```

## 📅 Scheduling

### Linux/macOS (cron)
```bash
crontab -e
# Daily at 8 AM
0 8 * * * cd /path/to/queryhub && ./queryhub run-report daily_sales
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Task
3. Set trigger and action
4. Action: `C:\path\to\queryhub.exe run-report REPORT_ID`

## 📚 Documentation

- **BUILD.md** - Build instructions
- **DISTRIBUTION.md** - Usage guide
- **README.md** - Full documentation
- **examples/README.md** - Example configurations
- **DOCKER_BUILD_SUMMARY.md** - Implementation details

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Permission denied | `chmod +x queryhub` |
| Provider not found | Check provider ID matches config |
| SMTP auth failed | For Gmail, use App Password |
| Template not found | Verify templates-dir path |
| DB connection failed | Check DSN and env vars |

## 💡 Tips

1. Always test with `--no-email` first
2. Use environment variables for secrets
3. Start with simple reports
4. Check examples directory
5. Run with `-v` for debugging
6. Keep config files secure (`chmod 600`)

## 🔗 Quick Links

- GitHub: https://github.com/isasnovich/QueryHub
- Issues: https://github.com/isasnovich/QueryHub/issues

---

**QueryHub** - Configuration-driven report automation made simple.

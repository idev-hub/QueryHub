# QueryHub - Standalone Distribution Guide

This is a **standalone executable distribution** of QueryHub that requires **no Python installation**. The executable is self-contained and ready to run on Linux, macOS, and Windows.

## 📦 What's Included

```
queryhub-distribution/
├── queryhub              # Main executable (Linux/macOS)
├── queryhub.exe          # Main executable (Windows)
├── queryhub.sh           # Unix wrapper script
├── queryhub.bat          # Windows wrapper script
├── templates/            # Jinja2 HTML templates
│   └── report.html.j2   # Default report template
├── config/               # Configuration examples
│   ├── smtp.yaml        # SMTP email configuration
│   ├── providers/
│   │   └── providers.yaml  # Data provider definitions
│   └── reports/
│       └── sample_report.yaml  # Sample report definition
├── examples/             # Additional configuration samples
├── README.md            # Full project documentation
├── DISTRIBUTION.md      # This file
├── CHANGELOG.md         # Version history
├── LICENSE              # MIT License
└── VERSION.txt          # Build information
```

## 🚀 Quick Start

### Linux / macOS

```bash
# 1. Extract the distribution
tar -xzf queryhub-*.tar.gz
cd queryhub-distribution

# 2. Make executable (first time only)
chmod +x queryhub queryhub.sh

# 3. Test the installation
./queryhub --help

# 4. List available reports
./queryhub list-reports --config-dir config --templates-dir templates

# 5. Run a sample report (without sending email)
./queryhub run-report sample_report \
  --config-dir config \
  --templates-dir templates \
  --no-email \
  --output-html output.html
```

### Windows

```cmd
REM 1. Extract the ZIP file
REM 2. Open Command Prompt or PowerShell in the distribution folder

REM 3. Test the installation
queryhub.exe --help

REM 4. List available reports
queryhub.exe list-reports --config-dir config --templates-dir templates

REM 5. Run a sample report
queryhub.exe run-report sample_report --config-dir config --templates-dir templates --no-email --output-html output.html
```

## ⚙️ Configuration

### Step 1: Set Up Configuration Directory

Copy the example configuration to your working directory:

```bash
# Create your project directory
mkdir my-reports
cd my-reports

# Copy configuration from distribution
cp -r /path/to/queryhub-distribution/config .
cp -r /path/to/queryhub-distribution/templates .

# Copy the executable
cp /path/to/queryhub-distribution/queryhub .  # Linux/macOS
# or
copy \path\to\queryhub-distribution\queryhub.exe .  # Windows
```

### Step 2: Configure SMTP Settings

Edit `config/smtp.yaml`:

```yaml
host: smtp.gmail.com      # Your SMTP server
port: 587                 # SMTP port
use_tls: false
starttls: true           # Enable STARTTLS
username: ${SMTP_USERNAME}  # Use environment variable
password: ${SMTP_PASSWORD}  # Use environment variable
default_from: reports@yourcompany.com
default_to:
  - team@yourcompany.com
```

### Step 3: Configure Data Providers

Edit `config/providers/providers.yaml`:

#### PostgreSQL Example
```yaml
providers:
  - id: my_postgres
    type: sql
    target:
      dsn: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/mydb
    credentials:
      type: username_password
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
```

#### CSV Example
```yaml
  - id: my_csv
    type: csv
    root_path: ./data     # Path to CSV files
    delimiter: ","
```

#### REST API Example
```yaml
  - id: my_api
    type: rest
    base_url: https://api.example.com/v1/
    credentials:
      type: bearer_token
      token: ${API_TOKEN}
```

### Step 4: Create a Report Definition

Create `config/reports/my_report.yaml`:

```yaml
id: my_report
title: My Custom Report
description: This is my custom report
template: report.html.j2

components:
  - id: sales_data
    title: Sales Overview
    provider: my_postgres
    query:
      text: |
        SELECT 
          date,
          SUM(amount) as total_sales,
          COUNT(*) as order_count
        FROM sales
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY date
        ORDER BY date DESC
    render:
      type: table
      options:
        columns: [date, total_sales, order_count]

  - id: sales_chart
    title: Sales Trend
    provider: my_postgres
    query:
      text: |
        SELECT date, SUM(amount) as amount
        FROM sales
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY date
        ORDER BY date
    render:
      type: chart
      options:
        chart_type: line
        x_field: date
        y_field: amount
        title: 30-Day Sales Trend

email:
  to:
    - manager@company.com
  subject_template: "Sales Report - {{ generated_at.strftime('%Y-%m-%d') }}"
```

### Step 5: Set Environment Variables

#### Linux / macOS
```bash
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export POSTGRES_USER="dbuser"
export POSTGRES_PASSWORD="dbpass"
export API_TOKEN="your-api-token"
```

#### Windows (Command Prompt)
```cmd
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set POSTGRES_USER=dbuser
set POSTGRES_PASSWORD=dbpass
```

#### Windows (PowerShell)
```powershell
$env:SMTP_USERNAME="your-email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:POSTGRES_USER="dbuser"
$env:POSTGRES_PASSWORD="dbpass"
```

## 🔧 Usage Examples

### List All Available Reports
```bash
./queryhub list-reports --config-dir config --templates-dir templates
```

### Run Report Without Email
```bash
./queryhub run-report my_report \
  --config-dir config \
  --templates-dir templates \
  --no-email \
  --output-html report.html
```

### Run Report and Send Email
```bash
./queryhub run-report my_report \
  --config-dir config \
  --templates-dir templates
```

### Verbose Logging
```bash
./queryhub run-report my_report \
  --config-dir config \
  --templates-dir templates \
  -v
```

### Using Relative Paths
```bash
# If executable is in your PATH or current directory
./queryhub run-report daily_sales \
  --config-dir ./config \
  --templates-dir ./templates \
  --output-html ./output/sales-$(date +%Y%m%d).html
```

## 📊 Supported Data Sources

### SQL Databases
- PostgreSQL
- MySQL/MariaDB
- SQLite
- Microsoft SQL Server
- Any SQLAlchemy-compatible database

Configuration:
```yaml
type: sql
target:
  dsn: "dialect+driver://user:pass@host:port/database"
```

### Azure Data Explorer (Kusto)
```yaml
type: adx
cluster_uri: https://your-cluster.kusto.windows.net
database: YourDatabase
credentials:
  type: managed_identity
```

### REST APIs
```yaml
type: rest
base_url: https://api.example.com/v1/
credentials:
  type: bearer_token
  token: ${API_TOKEN}
```

### CSV Files
```yaml
type: csv
root_path: ./data
delimiter: ","
```

## 📈 Visualization Types

### Tables
```yaml
render:
  type: table
  options:
    columns: [col1, col2, col3]
```

### Charts
Supported chart types:
- `bar` - Bar chart
- `line` - Line chart
- `scatter` - Scatter plot
- `pie` - Pie chart
- `area` - Area chart

```yaml
render:
  type: chart
  options:
    chart_type: bar
    x_field: category
    y_field: value
    color: series
    title: "My Chart"
```

### Text
```yaml
render:
  type: text
  options:
    template: "Total: {value}"
    value_path: data.total
```

## 🔐 Security Best Practices

1. **Never hardcode credentials** - Always use environment variables
2. **Use app-specific passwords** - For Gmail, generate an app password
3. **Limit permissions** - Give database users minimal required permissions
4. **Secure config files** - Set appropriate file permissions:
   ```bash
   chmod 600 config/smtp.yaml
   ```
5. **Use STARTTLS/TLS** - Enable encryption for email transmission
6. **Rotate credentials regularly** - Update passwords periodically

## 🐛 Troubleshooting

### "Permission denied" (Linux/macOS)
```bash
chmod +x queryhub
```

### "Cannot connect to database"
- Verify connection string in `config/providers/providers.yaml`
- Check environment variables are set
- Ensure database is accessible from your network
- Test connection with native client first

### "SMTP authentication failed"
- Verify SMTP credentials
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Check SMTP server settings (host, port, TLS)

### "Template not found"
- Ensure `--templates-dir` points to correct directory
- Verify template file exists in templates directory
- Check template filename in report YAML matches actual file

### "Provider not found"
- Ensure provider ID in report matches ID in `providers.yaml`
- Check provider configuration is valid YAML

### Verbose Logging
Add `-v` flag for detailed debugging:
```bash
./queryhub run-report my_report -v
```

## 📁 Project Structure for Production

Recommended directory structure:

```
my-queryhub-project/
├── queryhub              # Executable
├── config/
│   ├── smtp.yaml
│   ├── providers/
│   │   └── providers.yaml
│   └── reports/
│       ├── daily_sales.yaml
│       ├── weekly_summary.yaml
│       └── monthly_overview.yaml
├── templates/
│   ├── report.html.j2
│   └── custom_template.html.j2
├── data/
│   └── static_data.csv
├── output/               # For generated reports
└── logs/                 # For log files
```

## 🔄 Scheduling Reports

Use system schedulers to run reports automatically:

### Linux/macOS (cron)
```bash
# Edit crontab
crontab -e

# Run daily at 8 AM
0 8 * * * cd /path/to/project && ./queryhub run-report daily_sales --config-dir config --templates-dir templates

# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/project && ./queryhub run-report weekly_summary --config-dir config --templates-dir templates
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create New Task
3. Set trigger (schedule)
4. Set action: `C:\path\to\queryhub.exe run-report daily_sales --config-dir config --templates-dir templates`
5. Save and enable

## 📚 Additional Resources

- Full documentation: See `README.md`
- Examples: See `examples/` directory
- GitHub: https://github.com/isasnovich/QueryHub
- Issues: https://github.com/isasnovich/QueryHub/issues

## 📝 Version Information

Check your build version:
```bash
cat VERSION.txt
```

## 💡 Tips and Tricks

1. **Test without email first**: Use `--no-email --output-html` to preview
2. **Start simple**: Begin with one data source and one component
3. **Use meaningful IDs**: Name reports and components clearly
4. **Validate YAML**: Use online YAML validators before running
5. **Check logs**: Run with `-v` flag when debugging
6. **Backup configs**: Version control your configuration files
7. **Document custom queries**: Add comments in YAML files

## 🤝 Getting Help

If you encounter issues:

1. Check this documentation
2. Run with `-v` flag for detailed logs
3. Verify configuration files are valid YAML
4. Check environment variables are set correctly
5. Review the main `README.md` for detailed information
6. Open an issue on GitHub with logs and config (redact sensitive data)

---

**QueryHub** - Turn data into actionable reports with zero hassle.

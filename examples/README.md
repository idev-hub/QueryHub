# QueryHub Examples Guide

This directory contains comprehensive examples and templates for QueryHub configurations.

## 📁 Files Overview

### Configuration Examples

- **`providers_complete.yaml`** - Complete reference for all provider types
  - PostgreSQL, MySQL, SQLite, SQL Server
  - Azure Data Explorer (Kusto)
  - REST APIs with various authentication methods
  - CSV/TSV files
  - All credential types and connection options

- **`smtp_examples.yaml`** - Email configuration examples
  - Gmail (with App Password setup)
  - Microsoft 365 / Outlook
  - SendGrid, Amazon SES, Mailgun
  - Self-hosted SMTP servers
  - Testing configurations
  - Troubleshooting tips

### Report Examples

- **`report_daily_sales.yaml`** - Complete daily sales report
  - Multiple visualization types (tables, charts, metrics)
  - Revenue analytics and trends
  - Product performance
  - Regional distribution
  - Ready to use with minor modifications

- **`report_executive_dashboard.yaml`** - Weekly executive dashboard
  - Multi-source data integration (SQL + REST + CSV)
  - KPI tracking with comparisons
  - Comprehensive business metrics
  - Production-ready structure

## 🚀 Quick Start

### 1. Set Up a Simple Report

Start with the daily sales example:

```bash
# Copy example to your config
cp examples/report_daily_sales.yaml config/reports/my_sales_report.yaml

# Edit to match your database
vi config/reports/my_sales_report.yaml
```

Modify the provider references and SQL queries to match your database schema.

### 2. Configure Your Providers

```bash
# Use the complete examples as reference
cat examples/providers_complete.yaml

# Add your providers to config
vi config/providers/providers.yaml
```

Choose the providers you need:
- **SQL Database**: Use the PostgreSQL/MySQL/SQL Server examples
- **REST API**: Use the REST examples with your API details
- **CSV Files**: Use the CSV provider for static data

### 3. Set Up Email

```bash
# Copy SMTP example
cp examples/smtp_examples.yaml config/smtp.yaml

# Choose your email provider section and uncomment it
vi config/smtp.yaml
```

For Gmail (easiest for testing):
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use Gmail configuration from examples
4. Set environment variables

### 4. Test Your Configuration

```bash
# Set required environment variables
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export POSTGRES_USER="your-db-user"
export POSTGRES_PASSWORD="your-db-password"

# Test without email first
queryhub run-report my_sales_report \
  --config-dir config \
  --templates-dir templates \
  --no-email \
  --output-html test-report.html

# View the generated report
open test-report.html  # macOS
xdg-open test-report.html  # Linux
```

## 📊 Example Use Cases

### Simple CSV Report

Minimal setup, no database required:

```yaml
# config/providers/providers.yaml
providers:
  - id: my_csv
    type: csv
    root_path: ./data
    delimiter: ","
```

```yaml
# config/reports/csv_report.yaml
id: csv_report
title: CSV Data Report
components:
  - id: data_table
    title: My Data
    provider: my_csv
    query:
      path: mydata.csv
    render:
      type: table
      options:
        columns: [col1, col2, col3]
```

### PostgreSQL Analytics Report

Database-driven analytics:

```yaml
# config/providers/providers.yaml
providers:
  - id: my_postgres
    type: sql
    target:
      dsn: postgresql+asyncpg://user:pass@localhost:5432/mydb
    credentials:
      type: username_password
      username: ${DB_USER}
      password: ${DB_PASS}
```

```yaml
# config/reports/analytics.yaml
id: analytics_report
title: Analytics Report
components:
  - id: metrics
    title: Key Metrics
    provider: my_postgres
    query:
      text: |
        SELECT 
          date,
          count(*) as events,
          sum(value) as total
        FROM analytics
        WHERE date >= CURRENT_DATE - 7
        GROUP BY date
    render:
      type: chart
      options:
        chart_type: line
        x_field: date
        y_field: total
```

### REST API Integration

External API data:

```yaml
# config/providers/providers.yaml
providers:
  - id: my_api
    type: rest
    base_url: https://api.example.com/v1/
    credentials:
      type: bearer_token
      token: ${API_TOKEN}
```

```yaml
# config/reports/api_report.yaml
id: api_report
title: API Data Report
components:
  - id: api_data
    title: API Results
    provider: my_api
    query:
      endpoint: data
      params:
        from_date: "2024-01-01"
        limit: 100
    render:
      type: table
```

### Multi-Source Report

Combine different data sources:

```yaml
id: multi_source_report
title: Combined Report
components:
  # From database
  - id: db_metrics
    provider: postgres_db
    query:
      text: SELECT * FROM metrics
    render:
      type: table

  # From REST API
  - id: api_data
    provider: rest_api
    query:
      endpoint: stats
    render:
      type: chart
      options:
        chart_type: bar

  # From CSV file
  - id: csv_data
    provider: csv_local
    query:
      path: reference.csv
    render:
      type: table
```

## 🎨 Visualization Examples

### Tables

```yaml
render:
  type: table
  options:
    columns: [name, value, status]
    headers:
      name: Product Name
      value: Revenue
      status: Status
```

### Line Chart

```yaml
render:
  type: chart
  options:
    chart_type: line
    x_field: date
    y_field: value
    title: Trend Over Time
```

### Bar Chart

```yaml
render:
  type: chart
  options:
    chart_type: bar
    x_field: category
    y_field: amount
    color: region
```

### Pie Chart

```yaml
render:
  type: chart
  options:
    chart_type: pie
    label_field: category
    value_field: percentage
```

### Text/Metrics

```yaml
render:
  type: text
  options:
    template: "Total: {total:,.2f} | Average: {avg:.2f}"
```

## 🔒 Security Best Practices

### Environment Variables

Always use environment variables for sensitive data:

```yaml
# Good ✅
username: ${DB_USER}
password: ${DB_PASSWORD}
token: ${API_TOKEN}

# Bad ❌
username: myuser
password: mypassword123
```

### Set Environment Variables

```bash
# Linux/macOS
export DB_USER="myuser"
export DB_PASSWORD="secretpass"

# Windows Command Prompt
set DB_USER=myuser
set DB_PASSWORD=secretpass

# Windows PowerShell
$env:DB_USER="myuser"
$env:DB_PASSWORD="secretpass"
```

### Secure Config Files

```bash
# Restrict permissions
chmod 600 config/smtp.yaml
chmod 600 config/providers/providers.yaml

# Never commit secrets
echo "config/*.yaml" >> .gitignore
```

## 🐛 Troubleshooting

### Configuration Validation

```bash
# Test YAML syntax
python -c "import yaml; yaml.safe_load(open('config/reports/my_report.yaml'))"

# Validate report
queryhub list-reports --config-dir config
```

### Verbose Logging

```bash
# Enable debug output
queryhub run-report my_report -v
```

### Common Issues

**Provider not found:**
- Check provider ID in report matches providers.yaml
- Verify providers.yaml is in config/providers/

**Template not found:**
- Ensure templates directory exists
- Check template filename in report config

**Database connection failed:**
- Verify DSN connection string
- Check environment variables are set
- Test connection with database client

**SMTP authentication failed:**
- For Gmail, use App Password
- Verify credentials
- Check firewall/network settings

## 📚 Additional Resources

- [Main Documentation](../README.md)
- [Distribution Guide](../DISTRIBUTION.md)
- [Build Documentation](../BUILD.md)
- [Configuration Reference](../docs/reference/)

## 💡 Tips

1. **Start Simple**: Begin with one provider and one component
2. **Test Incrementally**: Add components one at a time
3. **Use --no-email**: Test report generation before sending emails
4. **Copy Examples**: Use these examples as templates
5. **Check Logs**: Use `-v` flag for detailed debugging

## 🤝 Contributing

Have a useful example? Contributions welcome!

1. Create your example configuration
2. Test it thoroughly
3. Add documentation
4. Submit a pull request

---

**Need help?** Open an issue at https://github.com/isasnovich/QueryHub/issues

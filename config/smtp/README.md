# SMTP Configuration

This folder contains SMTP server configurations for sending email reports.

## Structure

```
config/smtp/
  default.yaml      # Default SMTP configuration
  production.yaml   # Optional: Production SMTP settings
  staging.yaml      # Optional: Staging environment
  ...
```

## Usage

### Default Configuration

By default, QueryHub uses `config/smtp/default.yaml` if no specific SMTP config is specified in the report metadata.

### Per-Report Configuration

You can specify a different SMTP configuration in the report's `metadata.yaml`:

```yaml
id: my_report
title: My Report
smtp_config: production.yaml  # or just "production"
# ... other settings
```

### HTML-Only Mode

If no SMTP configuration is found and `--email` flag is not used, QueryHub operates in HTML-only mode and only generates the HTML output without sending emails.

### Email Mode Validation

When using the `--email` flag, QueryHub validates that an SMTP configuration is available:
- Looks for the SMTP config specified in `metadata.yaml`
- Falls back to `config/smtp/default.yaml` if not specified
- Raises an error if neither is found

## Configuration Format

See `default.yaml` for the complete configuration schema. Required fields:
- `host`: SMTP server hostname
- `port`: SMTP server port
- `default_from`: Default sender email address

Optional fields:
- `use_tls`: Enable TLS (default: false)
- `starttls`: Use STARTTLS (default: false)
- `username`: SMTP authentication username
- `password`: SMTP authentication password
- `default_to`: Default recipient list
- `subject_template`: Email subject template

## Environment Variables

You can use environment variable substitution in SMTP configs:

```yaml
host: smtp.example.com
username: ${SMTP_USERNAME:default_user}
password: ${SMTP_PASSWORD}
```

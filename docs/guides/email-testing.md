# Email Testing Guide

## Overview

This guide shows how to test QueryHub reports in email format by generating `.eml` files that can be opened in email clients.

## Running Email Tests

### Prerequisites

1. Docker containers must be running:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. Wait for PostgreSQL to be ready:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

### Generate Email File

Run the email generation test:

```bash
pytest tests/test_docker_integration.py::test_email_generation -v -s
```

This will:
1. Execute the report with all visualizations
2. Create an email message (MIME multipart/alternative)
3. Save it as `test_output/all_visualizations_email.eml`

### View Email

Open the generated `.eml` file:

**macOS:**
```bash
open test_output/all_visualizations_email.eml
```

**Linux:**
```bash
xdg-open test_output/all_visualizations_email.eml
```

**Windows:**
```bash
start test_output\all_visualizations_email.eml
```

The email will open in your default email client (Apple Mail, Outlook, Thunderbird, etc.)

## Email Structure

The generated email contains:

### Headers
- **Subject:** QueryHub - All Visualizations Report
- **From:** queryhub@example.com
- **To:** user@example.com
- **Date:** Current timestamp

### Content
- **Plain text version:** Simple text description for clients that don't support HTML
- **HTML version:** Full report with all visualizations

### MIME Structure
```
multipart/alternative
├── text/plain (fallback)
└── text/html (primary content)
```

## What to Test

When viewing the email, verify:

### Visual Elements
- ✅ KPI cards with gradient backgrounds
- ✅ Tables with proper formatting
- ✅ Text components with formatted numbers
- ✅ Ranked lists with medal colors (gold, silver, bronze)
- ✅ Progress bars showing percentages
- ✅ Product badges with status indicators
- ✅ Alert boxes with conditional styling

### Email Client Compatibility
- ✅ Inline styles are preserved
- ✅ Gradients render correctly (most modern clients)
- ✅ Grid layouts work (modern clients) or degrade gracefully
- ✅ Colors and borders display properly
- ✅ Emoji render correctly (⚠️, ✅, ⚡)

### Content Accuracy
- ✅ All 15 components are present
- ✅ Data values are correct
- ✅ Number formatting is applied (thousands separators)
- ✅ Conditional logic works (alert states)

## Email Clients

### Supported Clients

**Desktop:**
- Apple Mail ✅ (Excellent support)
- Outlook 2016+ ✅ (Good support)
- Thunderbird ✅ (Good support)
- Gmail (web) ✅ (Good support)

**Mobile:**
- iOS Mail ✅ (Excellent support)
- Gmail (Android/iOS) ✅ (Good support)
- Outlook (mobile) ✅ (Good support)

**Web:**
- Gmail ✅ (Good support)
- Outlook.com ✅ (Good support)
- Yahoo Mail ⚠️ (Limited gradient support)

### Known Limitations

**Outlook 2007-2013:**
- Limited gradient support
- Grid layout may not work (use tables instead)
- Some CSS properties ignored

**Older Email Clients:**
- May not support CSS3 gradients
- Complex layouts may break
- Fall back to basic styling

## Customizing Email Tests

### Change Email Headers

Edit the test in `tests/test_docker_integration.py`:

```python
msg['Subject'] = 'Your Custom Subject'
msg['From'] = 'your-sender@example.com'
msg['To'] = 'recipient@example.com'
```

### Add Attachments

```python
from email.mime.base import MIMEBase
from email import encoders

# Attach a file
with open('data.csv', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="data.csv"')
    msg.attach(part)
```

### Use Different Report

Change the report name:

```python
result = await executor.execute_report("sales_dashboard")
```

## Troubleshooting

### Email Won't Open
- **Issue:** `.eml` file doesn't open
- **Solution:** Set your default email client or use specific command:
  ```bash
  # macOS - Force Apple Mail
  open -a "Mail" test_output/all_visualizations_email.eml
  
  # Windows - Force Outlook
  outlook test_output\all_visualizations_email.eml
  ```

### HTML Not Rendering
- **Issue:** Email shows plain text only
- **Solution:** 
  - Ensure HTML email viewing is enabled in your client
  - Check that the HTML part is properly encoded
  - Try a different email client

### Styles Not Applied
- **Issue:** Email looks plain/unstyled
- **Solution:**
  - Verify inline styles are used (not external CSS)
  - Test in a different client
  - Check email client CSS support

### Images Not Loading
- **Issue:** Images don't display
- **Solution:**
  - Use inline images (base64 encoded) or
  - Use absolute URLs to hosted images
  - Note: QueryHub currently uses CSS gradients (no image files)

## Automated Testing

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Generate Email Test
  run: |
    pytest tests/test_docker_integration.py::test_email_generation -v
    
- name: Upload Email Artifact
  uses: actions/upload-artifact@v3
  with:
    name: test-email
    path: test_output/all_visualizations_email.eml
```

### Email Service Testing

For testing with actual email services (SendGrid, AWS SES, etc.), see the SMTP configuration guide.

## Best Practices

1. **Always test in multiple clients** - Email rendering varies significantly
2. **Use inline styles exclusively** - External CSS is stripped by most clients
3. **Provide plain text alternative** - For accessibility and client compatibility
4. **Keep HTML under 100KB** - Large emails may be truncated
5. **Test on mobile** - Many users read emails on mobile devices
6. **Use web-safe fonts** - Arial, Helvetica, Georgia, Times New Roman
7. **Avoid JavaScript** - Not supported in emails
8. **Test links** - Ensure all URLs are absolute and working

## Examples

See complete examples in:
- `tests/test_docker_integration.py::test_email_generation`
- `tests/fixtures/docker_integration/reports/all_visualizations.yaml`
- `docs/reference/html-visualizations.md`

## Further Reading

- [Email Client CSS Support](https://www.caniemail.com/)
- [HTML Email Best Practices](https://www.campaignmonitor.com/css/)
- [MIME Email Format](https://datatracker.ietf.org/doc/html/rfc2045)

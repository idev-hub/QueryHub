# Screenshot Images

This directory contains screenshot images for documentation.

## Required Screenshots

To complete the README documentation, add the following screenshots:

### 1. sales-dashboard-report.png
**Source:** `test_output/sales_dashboard_report.html`

**How to generate:**
```bash
# Run integration tests to generate the report
pytest tests/test_docker_integration.py::test_postgres_sales_report -v

# Open in browser and take screenshot
open test_output/sales_dashboard_report.html
```

**What to capture:** Full page screenshot showing:
- Report header with title and metadata
- Multiple components (tables, charts, KPI cards)
- Clean, professional email-ready styling

**Recommended dimensions:** 1200px wide (retina display recommended)

### 2. all-visualizations-report.png
**Source:** `test_output/all_visualizations_report.html`

**How to generate:**
```bash
# Run the all visualizations test
pytest tests/test_docker_integration.py::test_all_visualizations -v

# Open and screenshot
open test_output/all_visualizations_report.html
```

**What to capture:** Comprehensive view showing:
- Various table formats
- Chart examples (bar, line, scatter)
- Text components with formatting
- Custom HTML components
- Alert boxes and badges

**Recommended dimensions:** 1200px wide, full page or key sections

### 3. chart-visualizations-report.png
**Source:** `test_output/chart_visualizations_report.html`

**How to generate:**
```bash
# Run the chart visualizations test
pytest tests/test_docker_integration.py::test_chart_visualizations -v

# Open and screenshot
open test_output/chart_visualizations_report.html
```

**What to capture:** Focus on data visualization:
- Multiple Plotly charts
- Different chart types (bar, line, scatter)
- Color-coded data series
- Clean chart presentation

**Recommended dimensions:** 1200px wide

## Screenshot Tips

### Using Browser Developer Tools
1. Open HTML file in Chrome/Firefox
2. Press F12 to open DevTools
3. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)
4. Type "Capture full size screenshot" and press Enter
5. Save to this directory with the correct filename

### Using macOS Screenshot Tools
```bash
# Full window screenshot
open test_output/sales_dashboard_report.html
# Press Cmd+Shift+4, then press Space, then click the browser window
```

### Using Email Client
For email appearance screenshots:
```bash
# Open .eml file in email client
open test_output/all_visualizations_email.eml

# Take screenshot of email client showing the report
```

## Image Guidelines

- **Format:** PNG (for best quality)
- **Width:** 1200-1400px recommended
- **Compression:** Optimize images before committing (use ImageOptim, TinyPNG, etc.)
- **File size:** Keep under 500KB per image if possible
- **Naming:** Use exact filenames referenced in README.md
- **Retina:** Use retina display for crisp screenshots

## Alternative: Automated Screenshot Generation

For automated screenshot generation, consider using:

```python
# Using Playwright (example)
from playwright.sync_api import sync_playwright

def capture_report_screenshot(html_file: str, output_file: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.goto(f"file://{html_file}")
        page.screenshot(path=output_file, full_page=True)
        browser.close()

# Usage
capture_report_screenshot(
    "test_output/sales_dashboard_report.html",
    "docs/images/sales-dashboard-report.png"
)
```

## Verification

After adding screenshots, verify they display correctly:

```bash
# Preview README
open README.md  # in your markdown viewer
# Or on GitHub after committing
```

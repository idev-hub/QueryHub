# Report Examples

This directory contains HTML report examples for documentation.

## Available Examples

### 1. sales_dashboard_report.html
Business intelligence dashboard with sales metrics, regional performance, and customer feedback.

**Features:**
- Data tables with sales metrics
- Revenue and transaction charts
- Customer rating displays
- System health indicators

### 2. all_visualizations_report.html
Comprehensive showcase of all QueryHub visualization types.

**Features:**
- Multiple table formats (simple, aggregated, feedback)
- Text components with templating
- Custom HTML components
- KPI cards and metrics
- Lists and badges
- Alert boxes with conditional styling

### 3. chart_visualizations_report.html
Data visualization focused report with various Plotly chart types.

**Features:**
- Bar charts (revenue by region, product performance)
- Line charts (revenue trends, transaction counts)
- Scatter plots (units vs revenue, system health)
- Multi-dimensional data with color grouping
- Summary statistics table

## Viewing Examples

### In Browser
```bash
# Open from command line
open docs/images/sales_dashboard_report.html
open docs/images/all_visualizations_report.html
open docs/images/chart_visualizations_report.html

# Or navigate in browser to file:///path/to/QueryHub/docs/images/
```

### On GitHub
When viewing the README on GitHub, click the links to view the raw HTML files.

## Regenerating Examples

To update these examples with fresh data:

```bash
# Run integration tests
pytest tests/test_docker_integration.py -v -m integration

# Copy updated reports
cp test_output/sales_dashboard_report.html docs/images/
cp test_output/all_visualizations_report.html docs/images/
cp test_output/chart_visualizations_report.html docs/images/
```

## Notes

- These HTML files are self-contained and can be opened directly in any browser
- They include embedded Plotly JavaScript for interactive charts
- Email versions (.eml files) can be found in `test_output/` after running tests
- The reports use inline CSS for email client compatibility

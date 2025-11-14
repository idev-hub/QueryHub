# HTML Visualizations Reference

## Overview

QueryHub supports multiple visualization types that render as HTML and work perfectly in email reports. This document describes all available visualization types and their usage.

## Visualization Types

### 1. Table Renderer (`type: table`)

Renders query results as an HTML table with automatic column detection.

**Use cases:**
- Display tabular data
- Show detailed records
- List aggregated results

**Example:**
```yaml
- id: sales_table
  title: Sales Data
  provider: my_database
  query:
    text: SELECT region, product, revenue FROM sales
  render:
    type: table
```

### 2. Text Renderer (`type: text`)

Renders single values or formatted text with template support.

**Use cases:**
- Display KPIs and metrics
- Show single aggregated values
- Format numbers with custom templates

**Example:**
```yaml
- id: total_revenue
  title: Total Revenue
  provider: my_database
  query:
    text: SELECT SUM(revenue) as total FROM sales
  render:
    type: text
    options:
      template: "Total Revenue: {value:,.2f}"
      value_path: total
```

**Template formatting:**
- `{value}` - Raw value
- `{value:,.2f}` - Thousands separator with 2 decimals
- `{value:>10}` - Right-aligned, 10 characters wide

### 3. HTML Renderer (`type: html`)

Renders custom HTML using Jinja2 templates with full control over styling.

**Use cases:**
- Create custom card layouts
- Build progress bars and meters
- Design badges and status indicators
- Create alert boxes
- Build custom visualizations

**Example:**
```yaml
- id: kpi_cards
  title: Key Metrics
  provider: my_database
  query:
    text: |
      SELECT 
        COUNT(*) as total_orders,
        SUM(revenue) as total_revenue,
        AVG(revenue) as avg_order
      FROM orders
  render:
    type: html
    options:
      template: |
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
          <div style="background: #667eea; color: white; padding: 20px; border-radius: 8px;">
            <div style="font-size: 32px; font-weight: bold;">{{ total_orders }}</div>
            <div style="font-size: 14px;">Total Orders</div>
          </div>
          <div style="background: #f093fb; color: white; padding: 20px; border-radius: 8px;">
            <div style="font-size: 32px; font-weight: bold;">{{ "{:,.0f}".format(total_revenue) }}</div>
            <div style="font-size: 14px;">Total Revenue</div>
          </div>
          <div style="background: #4facfe; color: white; padding: 20px; border-radius: 8px;">
            <div style="font-size: 32px; font-weight: bold;">{{ "{:,.0f}".format(avg_order) }}</div>
            <div style="font-size: 14px;">Average Order</div>
          </div>
        </div>
```

## Email-Friendly HTML Components

All visualizations are designed to work in email clients. Follow these best practices:

### KPI Cards

Display key metrics in colorful gradient cards:

```yaml
render:
  type: html
  options:
    template: |
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
          <div style="font-size: 32px; font-weight: bold;">{{ metric_value }}</div>
          <div style="font-size: 14px; opacity: 0.9;">Metric Name</div>
        </div>
      </div>
```

### Ranked Lists

Show top items with medal-style rankings:

```yaml
render:
  type: html
  options:
    template: |
      <div style="font-family: Arial, sans-serif;">
        {% for row in data %}
        <div style="display: flex; align-items: center; padding: 12px; margin-bottom: 8px; 
                    background: {% if loop.index == 1 %}#ffd700{% elif loop.index == 2 %}#c0c0c0{% else %}#cd7f32{% endif %}20; 
                    border-left: 4px solid {% if loop.index == 1 %}#ffd700{% elif loop.index == 2 %}#c0c0c0{% else %}#cd7f32{% endif %};">
          <div style="font-size: 24px; font-weight: bold; width: 40px;">#{{ loop.index }}</div>
          <div style="flex: 1;">
            <div style="font-weight: bold;">{{ row.name }}</div>
            <div style="color: #666;">{{ row.value }}</div>
          </div>
        </div>
        {% endfor %}
      </div>
```

### Progress Bars

Visualize percentages and distributions:

```yaml
render:
  type: html
  options:
    template: |
      <div style="font-family: Arial, sans-serif;">
        {% for row in data %}
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-weight: 500;">{{ row.category }}</span>
            <span style="color: #666;">{{ "{:.1f}".format(row.percentage) }}%</span>
          </div>
          <div style="background: #e0e0e0; height: 24px; border-radius: 12px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); 
                        height: 100%; width: {{ row.percentage }}%;"></div>
          </div>
        </div>
        {% endfor %}
      </div>
```

### Badge Lists

Show items with status badges:

```yaml
render:
  type: html
  options:
    template: |
      <div style="display: flex; flex-wrap: wrap; gap: 12px;">
        {% for row in data %}
        <div style="padding: 16px; border: 2px solid #94a3b8; border-radius: 8px;">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: bold;">{{ row.name }}</span>
            <span style="background: #10b981; color: white; padding: 4px 8px; 
                        border-radius: 12px; font-size: 11px;">{{ row.status }}</span>
          </div>
          <div style="color: #666; margin-top: 8px;">{{ row.details }}</div>
        </div>
        {% endfor %}
      </div>
```

### Alert Boxes

Display contextual alerts based on data conditions:

```yaml
render:
  type: html
  options:
    template: |
      <div style="font-family: Arial, sans-serif;">
        {% if data[0].error_count > 0 %}
        <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 16px; border-radius: 4px;">
          <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 20px; margin-right: 8px;">⚠️</span>
            <span style="font-weight: bold; color: #dc2626;">Critical Alert</span>
          </div>
          <p style="margin: 0; color: #991b1b;">{{ data[0].error_count }} errors detected</p>
        </div>
        {% else %}
        <div style="background: #d1fae5; border-left: 4px solid #10b981; padding: 16px; border-radius: 4px;">
          <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 20px; margin-right: 8px;">✅</span>
            <span style="font-weight: bold; color: #059669;">All Systems Operational</span>
          </div>
          <p style="margin: 0; color: #065f46;">Everything is running smoothly</p>
        </div>
        {% endif %}
      </div>
```

## Jinja2 Template Features

The HTML renderer uses Jinja2 templating with these features:

### Variables
- `data` - List of query result rows (list of dicts)
- `result` - Raw query result
- For single-row queries, all fields are available directly: `{{ field_name }}`

### Loops
```jinja2
{% for row in data %}
  {{ row.column_name }}
  {{ loop.index }}  {# 1-based index #}
  {{ loop.first }}  {# True on first iteration #}
  {{ loop.last }}   {# True on last iteration #}
{% endfor %}
```

### Conditionals
```jinja2
{% if condition %}
  ...
{% elif other_condition %}
  ...
{% else %}
  ...
{% endif %}
```

### Filters and Formatting
```jinja2
{{ value|round }}
{{ "{:,.2f}".format(number) }}  {# Thousands separator, 2 decimals #}
{{ "{:.1f}".format(percentage) }}  {# 1 decimal place #}
```

## Email Compatibility Guidelines

For maximum email client compatibility:

1. **Use inline styles** - All CSS must be inline
2. **Use tables for layout** (optional) - Grid layouts work in most modern clients
3. **Use web-safe fonts** - Arial, Helvetica, Georgia, Times New Roman
4. **Avoid JavaScript** - Not supported in emails
5. **Use absolute URLs** - For any external resources
6. **Test gradient support** - Linear gradients work in most clients
7. **Limit width** - Keep content under 600px for mobile
8. **Use emoji carefully** - Some clients don't support all emoji

## Color Schemes

### Status Colors
- Success: `#10b981` (green)
- Warning: `#f59e0b` (orange)
- Error: `#ef4444` (red)
- Info: `#3b82f6` (blue)

### Gradient Examples
```css
/* Purple gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Pink gradient */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

/* Blue gradient */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);

/* Green gradient */
background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
```

## Examples

See the complete examples in:
- `tests/fixtures/docker_integration/reports/all_visualizations.yaml`
- `test_output/all_visualizations_report.html` (after running integration tests)

## Testing

Run integration tests to see all visualizations:

```bash
# Start containers
make docker-up

# Run visualization tests
pytest tests/test_docker_integration.py::test_all_visualizations -v

# View the generated report
open test_output/all_visualizations_report.html
```

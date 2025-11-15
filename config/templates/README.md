# QueryHub Templates

This directory contains Jinja2 templates for rendering reports.

## Default Template

- **report.html.j2** - The default HTML report template

## Using Templates

Templates are referenced by filename in the report's `metadata.yaml`:

```yaml
# config/reports/my_report/metadata.yaml
id: my_report
title: My Report
template: report.html.j2  # Filename in config/templates/
```

## Custom Template Folder

You can override the default template folder in metadata.yaml:

```yaml
# Use a custom template folder (relative or absolute path)
template_folder: ../../../custom_templates
template: my_custom_template.html.j2
```

## Template Variables

Templates have access to:
- `title` - Report title
- `description` - Report description
- `generated_at` - Timestamp of report generation
- `components` - List of rendered component results
- Custom variables from your report configuration

## Creating Custom Templates

Copy `report.html.j2` as a starting point:

```bash
cp config/templates/report.html.j2 config/templates/my_template.html.j2
```

Then edit to customize the layout and styling.

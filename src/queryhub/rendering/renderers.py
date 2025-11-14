"""HTML component renderers."""

from __future__ import annotations

import html
from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping

from ..config.models import ComponentRenderConfig, ComponentRendererType, QueryComponentConfig
from ..core.errors import RenderingError
from ..providers.base import QueryResult


class ComponentRenderer(ABC):
    """Transform a query result into HTML (Strategy Pattern)."""

    @abstractmethod
    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render the component into HTML."""

    def _escape(self, value: Any) -> str:
        """Safely escape HTML content."""
        return html.escape(str(value))

    def _render_empty_state(self, message: str, css_class: str) -> str:
        """Render an empty state message."""
        return f'<div class="component {css_class} empty">{self._escape(message)}</div>'


class DataExtractor:
    """Extract and normalize data from query results (SRP)."""

    @staticmethod
    def ensure_rows(data: Any) -> list[Mapping[str, Any]]:
        """Ensure data is in list-of-dict format."""
        if data is None:
            return []
        if isinstance(data, list):
            if not data or isinstance(data[0], Mapping):
                return [dict(item) for item in data]
        if isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
            rows = []
            for item in data:
                if isinstance(item, Mapping):
                    rows.append(dict(item))
            return rows
        return []

    @staticmethod
    def extract_columns(data: list[Mapping[str, Any]], specified_columns: list[str] | None = None) -> list[str]:
        """Extract column names from data."""
        if specified_columns:
            return specified_columns
        if data:
            return list(data[0].keys())
        return []

    @staticmethod
    def traverse_path(data: Any, path: str) -> Any:
        """Traverse nested data structure by path."""
        current = data
        for segment in path.split("."):
            if isinstance(current, Mapping):
                current = current.get(segment)
            elif isinstance(current, list):
                try:
                    index = int(segment)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
        return current


class TableRenderer(ComponentRenderer):
    """Render list-of-dict data into an HTML table."""

    def __init__(self) -> None:
        self._extractor = DataExtractor()

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render tabular data as HTML table."""
        records = self._extractor.ensure_rows(result.data)
        if not records:
            return self._render_empty_state("No data available", "component-table")

        columns = self._extractor.extract_columns(
            records,
            component.render.options.get("columns"),
        )

        table_html = self._build_table(component, records, columns)
        return f'<div class="component component-table">{table_html}</div>'

    def _build_table(
        self,
        component: QueryComponentConfig,
        records: list[Mapping[str, Any]],
        columns: list[str],
    ) -> str:
        """Build HTML table structure."""
        title = self._escape(component.title or component.id)
        header = self._build_header(columns)
        body = self._build_body(records, columns)

        return f"<h3>{title}</h3><table><thead>{header}</thead><tbody>{body}</tbody></table>"

    def _build_header(self, columns: list[str]) -> str:
        """Build table header row."""
        cells = "".join(f"<th>{self._escape(col)}</th>" for col in columns)
        return f"<tr>{cells}</tr>"

    def _build_body(self, records: list[Mapping[str, Any]], columns: list[str]) -> str:
        """Build table body rows."""
        rows = []
        for row in records:
            cells = "".join(
                f"<td>{self._escape(row.get(col, ''))}</td>" for col in columns
            )
            rows.append(f"<tr>{cells}</tr>")
        return "".join(rows)


class ChartRenderer(ComponentRenderer):
    """Render chart widgets using Plotly (depends on optional library)."""

    def __init__(self, email_mode: bool = False) -> None:
        self._extractor = DataExtractor()
        self._email_mode = email_mode

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render data as interactive chart or static image for email."""
        records = self._extractor.ensure_rows(result.data)
        if not records:
            return self._render_empty_state("No chart data available", "component-chart")

        options = component.render.options
        chart_type = options.get("chart_type", "bar")
        x_field = options.get("x_field")
        y_field = options.get("y_field")
        
        if not x_field or not y_field:
            raise RenderingError("Chart renderer requires 'x_field' and 'y_field' options")

        figure = self._create_chart(records, chart_type, x_field, y_field, options, component.title)
        
        if self._email_mode:
            # Convert to static image for email compatibility
            html_snippet = self._figure_to_static_html(figure, component.title)
        else:
            # Interactive HTML with JavaScript
            html_snippet = figure.to_html(include_plotlyjs=False, full_html=False)
        
        return f'<div class="component component-chart">{html_snippet}</div>'

    def _create_chart(
        self,
        records: list[Mapping[str, Any]],
        chart_type: str,
        x_field: str,
        y_field: str,
        options: Mapping[str, Any],
        title: str | None,
    ) -> Any:
        """Create Plotly chart figure."""
        try:
            import plotly.express as px
        except ImportError as exc:
            raise RenderingError(
                "Plotly dependency missing. Install the 'charts' extra."
            ) from exc

        chart_func = getattr(px, chart_type, None)
        if chart_func is None:
            raise RenderingError(f"Unsupported chart type: {chart_type}")

        color = options.get("color")
        return chart_func(records, x=x_field, y=y_field, color=color, title=title)

    def _figure_to_static_html(self, figure: Any, title: str | None) -> str:
        """Convert Plotly figure to static image embedded in HTML."""
        try:
            import plotly.io as pio
            import base64
            
            # Export figure as PNG image
            img_bytes = pio.to_image(figure, format="png", width=800, height=500)
            
            # Convert to base64 for embedding in HTML
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Create HTML with embedded image
            title_html = f"<h3>{self._escape(title or 'Chart')}</h3>" if title else ""
            return f'{title_html}<img src="data:image/png;base64,{img_base64}" alt="{self._escape(title or "Chart")}" style="max-width: 100%; height: auto;" />'
        except Exception as exc:
            raise RenderingError(f"Failed to generate static chart image: {exc}") from exc


class TextRenderer(ComponentRenderer):
    """Render free-form text blocks with template support."""

    def __init__(self) -> None:
        self._extractor = DataExtractor()

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render text content with optional templating."""
        options = component.render.options
        value = self._extract_value(result.data, options)
        
        if isinstance(value, (dict, list)):
            import json
            value = json.dumps(value, indent=2)

        body = self._format_text(value, options)
        title = self._escape(component.title or component.id)
        
        return (
            '<div class="component component-text">'
            f"<h3>{title}</h3>"
            f'<div class="text-body">{body}</div>'
            "</div>"
        )

    def _extract_value(self, data: Any, options: Mapping[str, Any]) -> Any:
        """Extract value from data using path or key."""
        value_path = options.get("value_path")
        
        # If data is a list of records, get the first one
        if isinstance(data, list) and data:
            data = data[0]
        
        if value_path:
            return self._extractor.traverse_path(data, value_path)
        
        if isinstance(data, Mapping):
            value_key = options.get("value_key", "value")
            return data.get(value_key)
        
        return data

    def _format_text(self, value: Any, options: Mapping[str, Any]) -> str:
        """Format text using template."""
        template = options.get("template", "{value}")
        try:
            # Escape any dollar signs that aren't part of format specs
            # Then apply the format
            formatted = template.format(value=value)
            return formatted
        except (ValueError, KeyError):
            # If formatting fails, return the value as-is
            return str(value)


class HtmlRenderer(ComponentRenderer):
    """Render custom HTML with Jinja2 template support."""

    def __init__(self) -> None:
        self._extractor = DataExtractor()

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render custom HTML content with Jinja2 templating."""
        from jinja2 import Template, TemplateSyntaxError, UndefinedError

        options = component.render.options
        template_str = options.get("template", "")
        
        if not template_str:
            return self._render_empty_state("No HTML template provided", "component-html")

        # Prepare data for template
        records = self._extractor.ensure_rows(result.data)
        
        # If there's a single row and data is expected to be extracted, provide both
        context = {
            "data": records,
            "result": result.data,
        }
        
        # Add individual fields from first row if available
        if records and len(records) == 1:
            context.update(records[0])

        try:
            template = Template(template_str)
            rendered_html = template.render(**context)
            title = self._escape(component.title or component.id)
            
            return (
                '<div class="component component-html">'
                f"<h3>{title}</h3>"
                f'<div class="html-body">{rendered_html}</div>'
                "</div>"
            )
        except (TemplateSyntaxError, UndefinedError) as exc:
            raise RenderingError(f"HTML template rendering failed: {exc}") from exc


class RendererRegistry:
    """Map renderer types to concrete implementations (Registry Pattern)."""

    def __init__(self, renderers: Mapping[ComponentRendererType, ComponentRenderer] | None = None) -> None:
        self._renderers: dict[ComponentRendererType, ComponentRenderer] = dict(renderers or {})

    def register(self, renderer_type: ComponentRendererType, renderer: ComponentRenderer) -> None:
        """Register a renderer for a type."""
        self._renderers[renderer_type] = renderer

    def resolve(self, render_config: ComponentRenderConfig) -> ComponentRenderer:
        """Resolve renderer by configuration."""
        renderer = self._renderers.get(render_config.type)
        if renderer is None:
            raise RenderingError(f"Renderer for type {render_config.type} not registered")
        return renderer


def create_default_renderer_registry(email_mode: bool = False) -> RendererRegistry:
    """Return a renderer registry populated with built-in renderers.
    
    Args:
        email_mode: If True, charts will be rendered as static images for email compatibility.
    """
    registry = RendererRegistry()
    registry.register(ComponentRendererType.TABLE, TableRenderer())
    registry.register(ComponentRendererType.CHART, ChartRenderer(email_mode=email_mode))
    registry.register(ComponentRendererType.TEXT, TextRenderer())
    registry.register(ComponentRendererType.HTML, HtmlRenderer())
    return registry

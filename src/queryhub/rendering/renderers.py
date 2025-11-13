"""HTML component renderers."""

from __future__ import annotations

import html
from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping

from ..config.models import ComponentRenderConfig, ComponentRendererType, QueryComponentConfig
from ..providers.base import QueryResult


class ComponentRenderer(ABC):
    """Transform a query result into HTML."""

    @abstractmethod
    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        """Render the component into HTML."""


class TableRenderer(ComponentRenderer):
    """Render list-of-dict data into an HTML table."""

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        records = self._ensure_rows(result.data)
        if not records:
            return "<div class=\"component component-table empty\">No data available</div>"

        headers = component.render.options.get("columns")
        if not headers:
            headers = list(records[0].keys())

        body_rows = []
        for row in records:
            cells = "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in headers)
            body_rows.append(f"<tr>{cells}</tr>")
        header_cells = "".join(f"<th>{html.escape(str(col))}</th>" for col in headers)
        table_html = (
            "<div class=\"component component-table\">"
            f"<h3>{html.escape(component.title or component.id)}</h3>"
            "<table>"
            f"<thead><tr>{header_cells}</tr></thead>"
            f"<tbody>{''.join(body_rows)}</tbody>"
            "</table>"
            "</div>"
        )
        return table_html

    def _ensure_rows(self, data: Any) -> list[Mapping[str, Any]]:
        if data is None:
            return []
        if isinstance(data, list) and (not data or isinstance(data[0], Mapping)):
            return [dict(item) for item in data]
        if isinstance(data, Iterable):
            rows = []
            for item in data:
                if isinstance(item, Mapping):
                    rows.append(dict(item))
            return rows
        return []


class ChartRenderer(ComponentRenderer):
    """Render chart widgets using Plotly."""

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        records = TableRenderer()._ensure_rows(result.data)
        if not records:
            return "<div class=\"component component-chart empty\">No chart data available</div>"

        options = component.render.options
        chart_type = options.get("chart_type", "bar")
        x_field = options.get("x_field")
        y_field = options.get("y_field")
        color = options.get("color")
        if not x_field or not y_field:
            raise ValueError("Chart renderer requires 'x_field' and 'y_field' options")

        try:
            import plotly.express as px
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError("Plotly dependency missing. Install the 'charts' extra.") from exc

        chart_func = getattr(px, chart_type, None)
        if chart_func is None:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        figure = chart_func(records, x=x_field, y=y_field, color=color, title=component.title)
        html_snippet = figure.to_html(include_plotlyjs=False, full_html=False)
        return f"<div class=\"component component-chart\">{html_snippet}</div>"


class TextRenderer(ComponentRenderer):
    """Render free-form text blocks."""

    def render(self, component: QueryComponentConfig, result: QueryResult) -> str:
        template_text = component.render.options.get("template") or "{value}"
        value_key = component.render.options.get("value_key", "value")
        value_path = component.render.options.get("value_path")

        if value_path:
            value = self._traverse_path(result.data, value_path)
        elif isinstance(result.data, Mapping):
            value = result.data.get(value_key)
        else:
            value = result.data

        if isinstance(value, (dict, list)):
            import json

            value = json.dumps(value, indent=2)

        body = template_text.format(value=value)
        return (
            "<div class=\"component component-text\">"
            f"<h3>{html.escape(component.title or component.id)}</h3>"
            f"<div class=\"text-body\">{body}</div>"
            "</div>"
        )

    def _traverse_path(self, data: Any, path: str) -> Any:
        current = data
        for segment in path.split("."):
            if isinstance(current, Mapping):
                current = current.get(segment)
            elif isinstance(current, list):
                try:
                    index = int(segment)
                except ValueError:
                    return None
                if index >= len(current):
                    return None
                current = current[index]
            else:
                return None
        return current


class RendererRegistry:
    """Map renderer types to concrete implementations."""

    _lookup = {
        ComponentRendererType.TABLE: TableRenderer(),
        ComponentRendererType.CHART: ChartRenderer(),
        ComponentRendererType.TEXT: TextRenderer(),
    }

    def resolve(self, render_config: ComponentRenderConfig) -> ComponentRenderer:
        renderer = self._lookup.get(render_config.type)
        if renderer is None:
            raise KeyError(f"Renderer for type {render_config.type} not registered")
        return renderer

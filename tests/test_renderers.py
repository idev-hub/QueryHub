"""Renderer-specific unit tests."""

from __future__ import annotations

from queryhub.config.models import ComponentRenderConfig, ComponentRendererType, QueryComponentConfig
from queryhub.providers.base import QueryResult
from queryhub.rendering.renderers import RendererRegistry, TableRenderer, TextRenderer


def _build_component(render_config: ComponentRenderConfig) -> QueryComponentConfig:
    return QueryComponentConfig.model_validate(
        {
            "id": "text_component",
            "provider": "rest_weather",
            "query": {},
            "render": render_config.model_dump(),
        }
    )


def test_text_renderer_value_path() -> None:
    render_config = ComponentRenderConfig(
        type=ComponentRendererType.TEXT,
        options={
            "template": "Temp: {value}°C",
            "value_path": "current.temperature",
        },
    )
    component = _build_component(render_config)
    renderer = TextRenderer()
    result = QueryResult(data={"current": {"temperature": 23.5}})

    html = renderer.render(component, result)

    assert "Temp: 23.5°C" in html


def test_renderer_registry_table() -> None:
    registry = RendererRegistry()
    registry.register(ComponentRendererType.TABLE, TableRenderer())
    render_config = ComponentRenderConfig(type=ComponentRendererType.TABLE, options={})
    renderer = registry.resolve(render_config)
    assert renderer is not None

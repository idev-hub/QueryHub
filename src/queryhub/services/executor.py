"""Orchestrate report execution and rendering."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ..config import ConfigLoader
from ..config.models import QueryComponentConfig, ReportConfig, SMTPConfig, Settings
from ..providers import ProviderFactory, ProviderExecutionError, QueryProvider, QueryResult
from ..rendering import RendererRegistry, build_environment

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ComponentExecutionResult:
    """Result of executing a report component."""

    component: QueryComponentConfig
    result: QueryResult | None
    rendered_html: str | None
    error: Exception | None
    attempts: int
    duration_seconds: float


@dataclass(slots=True)
class ReportExecutionResult:
    """Aggregate outcome for a report run."""

    report: ReportConfig
    generated_at: datetime
    html: str
    components: List[ComponentExecutionResult]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_failures(self) -> bool:
        return any(item.error for item in self.components)


class ReportExecutor:
    """High level interface for producing HTML reports."""

    def __init__(
        self,
        settings: Settings,
        templates_dir: Path,
        *,
        auto_reload_templates: bool = False,
    ) -> None:
        self._settings = settings
        self._provider_factory = ProviderFactory(settings.providers)
        self._providers: dict[str, QueryProvider] = {}
        self._renderer_registry = RendererRegistry()
        self._templates_dir = Path(templates_dir)
        self._jinja_env = build_environment(self._templates_dir, auto_reload=auto_reload_templates)
        self._lock = asyncio.Lock()

    @classmethod
    async def from_config_dir(
        cls,
        config_dir: Path | str,
        *,
        templates_dir: Path | str,
        auto_reload_templates: bool = False,
    ) -> "ReportExecutor":
        loader = ConfigLoader(Path(config_dir))
        settings = await loader.load()
        return cls(settings, Path(templates_dir), auto_reload_templates=auto_reload_templates)

    async def execute_report(self, report_id: str) -> ReportExecutionResult:
        report = self._settings.reports.get(report_id)
        if report is None:
            raise KeyError(f"Report '{report_id}' not found")

        tasks = [self._run_component(report, component) for component in report.components]
        component_results = await asyncio.gather(*tasks)

        component_payloads: list[dict[str, Any]] = []
        rendered_components: list[ComponentExecutionResult] = []
        for item in component_results:
            rendered_components.append(item)
            component_payloads.append(
                {
                    "id": item.component.id,
                    "title": item.component.title,
                    "rendered": item.rendered_html,
                    "error": item.error,
                    "metadata": item.result.metadata if item.result else {},
                    "data": item.result.data if item.result else None,
                }
            )

        context = {
            "report": report,
            "generated_at": datetime.now(tz=timezone.utc),
            "components": component_payloads,
        }
        template = self._jinja_env.get_template(report.template)
        html = await template.render_async(context)

        generated_at = context["generated_at"]
        metadata = {
            "component_count": len(component_results),
            "failures": [item.component.id for item in component_results if item.error],
        }
        return ReportExecutionResult(
            report=report,
            generated_at=generated_at,
            html=html,
            components=rendered_components,
            metadata=metadata,
        )

    @property
    def settings(self) -> Settings:
        """Expose loaded settings for downstream consumers."""

        return self._settings

    @property
    def smtp_config(self) -> SMTPConfig:
        """Convenience accessor for SMTP configuration."""

        return self._settings.smtp

    async def shutdown(self) -> None:
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning("Failed to close provider %s: %s", provider, exc)

    async def _run_component(
        self, report: ReportConfig, component: QueryComponentConfig
    ) -> ComponentExecutionResult:
        start = time.perf_counter()
        attempts = 0
        provider = await self._resolve_provider(component.provider_id)
        timeout = component.timeout_seconds or provider.config.default_timeout_seconds
        max_attempts = component.retries if component.retries is not None else provider.config.retry_attempts
        backoff = provider.config.retry_backoff_seconds
        error: Exception | None = None
        result: QueryResult | None = None

        for attempt in range(max_attempts or 1):
            attempts = attempt + 1
            try:
                coro = provider.execute(component.query)
                result = await asyncio.wait_for(coro, timeout=timeout) if timeout else await coro
                error = None
                break
            except asyncio.TimeoutError as exc:
                error = ProviderExecutionError(f"Component '{component.id}' timed out")
                _LOGGER.error("Timeout executing component %s: %s", component.id, exc)
            except Exception as exc:  # noqa: BLE001
                error = ProviderExecutionError(f"Component '{component.id}' failed: {exc}")
                _LOGGER.exception("Error executing component %s", component.id)
            if attempt < (max_attempts - 1):
                await asyncio.sleep(backoff * (attempt + 1))

        rendered_html: str | None = None
        if not error and result is not None:
            try:
                renderer = self._renderer_registry.resolve(component.render)
                rendered_html = renderer.render(component, result)
            except Exception as exc:  # noqa: BLE001
                error = ProviderExecutionError(f"Rendering failed: {exc}")
                _LOGGER.exception("Rendering failure for component %s", component.id)

        duration = time.perf_counter() - start
        return ComponentExecutionResult(
            component=component,
            result=result,
            rendered_html=rendered_html,
            error=error,
            attempts=attempts,
            duration_seconds=duration,
        )

    async def _resolve_provider(self, provider_id: str) -> QueryProvider:
        provider = self._providers.get(provider_id)
        if provider is not None:
            return provider
        async with self._lock:
            provider = self._providers.get(provider_id)
            if provider is not None:
                return provider
            provider = self._provider_factory.create(provider_id)
            self._providers[provider_id] = provider
        return provider

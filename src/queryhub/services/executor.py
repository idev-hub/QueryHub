"""Orchestrate report execution and rendering."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ..config.models import ReportConfig, SMTPConfig, Settings
from ..core.contracts import ProviderFactoryProtocol, RendererResolverProtocol, ReportTemplateEngine
from .component_executor import ComponentExecutionResult, ComponentExecutor, ProviderResolver

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ReportExecutionResult:
    """Aggregate outcome for a report run (immutable)."""

    report: ReportConfig
    generated_at: datetime
    html: str
    components: List[ComponentExecutionResult]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_failures(self) -> bool:
        """Check if any component failed."""
        return any(not item.is_success for item in self.components)

    @property
    def success_count(self) -> int:
        """Count successful components."""
        return sum(1 for item in self.components if item.is_success)

    @property
    def failure_count(self) -> int:
        """Count failed components."""
        return len(self.components) - self.success_count


class ReportExecutor:
    """High level interface for producing HTML reports (follows SRP)."""

    def __init__(
        self,
        settings: Settings,
        *,
        provider_factory: ProviderFactoryProtocol,
        renderer_resolver: RendererResolverProtocol,
        template_engine: ReportTemplateEngine,
    ) -> None:
        self._settings = settings
        self._template_engine = template_engine
        self._provider_resolver = ProviderResolver(provider_factory)
        self._component_executor = ComponentExecutor(
            self._provider_resolver,
            renderer_resolver,
        )

    @classmethod
    async def from_config_dir(
        cls,
        config_dir: Path | str,
        *,
        templates_dir: Path | str,
        auto_reload_templates: bool = False,
        email_mode: bool = False,
    ) -> "ReportExecutor":
        """Factory method for creating executor from config directory.

        Args:
            config_dir: Path to configuration directory
            templates_dir: Path to templates directory
            auto_reload_templates: If True, reload templates on each render
            email_mode: If True, render charts as static images for email compatibility
        """
        from .application import QueryHubApplicationBuilder

        builder = QueryHubApplicationBuilder(
            config_dir=Path(config_dir),
            templates_dir=Path(templates_dir),
            auto_reload_templates=auto_reload_templates,
            email_mode=email_mode,
        )
        return await builder.create_executor()

    async def execute_report(self, report_id: str) -> ReportExecutionResult:
        """Execute a complete report with all components."""
        report = self._get_report(report_id)
        components = await self._execute_components(report)
        html = await self._render_report(report, components)

        return self._build_result(report, components, html)

    @property
    def settings(self) -> Settings:
        """Expose loaded settings for downstream consumers."""
        return self._settings

    @property
    def smtp_config(self) -> SMTPConfig:
        """Convenience accessor for SMTP configuration."""
        return self._settings.smtp

    async def shutdown(self) -> None:
        """Cleanup all resources."""
        await self._provider_resolver.close_all()

    def _get_report(self, report_id: str) -> ReportConfig:
        """Retrieve report configuration."""
        report = self._settings.reports.get(report_id)
        if report is None:
            raise KeyError(f"Report '{report_id}' not found")
        return report

    async def _execute_components(
        self,
        report: ReportConfig,
    ) -> List[ComponentExecutionResult]:
        """Execute all report components in parallel."""
        tasks = [self._component_executor.execute(component) for component in report.components]
        return await asyncio.gather(*tasks)

    async def _render_report(
        self,
        report: ReportConfig,
        components: List[ComponentExecutionResult],
    ) -> str:
        """Render the full report HTML."""
        component_payloads = self._build_component_payloads(components)
        context = {
            "report": report,
            "generated_at": datetime.now(tz=timezone.utc),
            "components": component_payloads,
        }
        return await self._template_engine.render(report, context)

    def _build_component_payloads(
        self,
        components: List[ComponentExecutionResult],
    ) -> list[dict[str, Any]]:
        """Transform component results into template context."""
        payloads: list[dict[str, Any]] = []
        for item in components:
            payloads.append(
                {
                    "id": item.component.id,
                    "title": item.component.title,
                    "rendered": item.rendered_html,
                    "error": item.error,
                    "metadata": item.result.metadata if item.result else {},
                    "data": item.result.data if item.result else None,
                }
            )
        return payloads

    def _build_result(
        self,
        report: ReportConfig,
        components: List[ComponentExecutionResult],
        html: str,
    ) -> ReportExecutionResult:
        """Build final execution result."""
        metadata = {
            "component_count": len(components),
            "failures": [item.component.id for item in components if not item.is_success],
            "total_duration": sum(item.duration_seconds for item in components),
        }
        return ReportExecutionResult(
            report=report,
            generated_at=datetime.now(tz=timezone.utc),
            html=html,
            components=components,
            metadata=metadata,
        )

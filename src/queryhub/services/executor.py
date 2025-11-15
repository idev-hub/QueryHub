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
        _LOGGER.info("Starting report execution for report_id='%s'", report_id)
        report = self._get_report(report_id)
        _LOGGER.info(
            "Report loaded: '%s' with %d component(s)",
            report.title,
            len(report.components),
        )
        
        _LOGGER.debug("Executing report components in parallel")
        components = await self._execute_components(report)
        
        _LOGGER.debug("Rendering report HTML template")
        html = await self._render_report(report, components)
        _LOGGER.debug("Report HTML rendered successfully (size: %d bytes)", len(html))

        result = self._build_result(report, components, html)
        _LOGGER.info(
            "Report execution completed: success=%d, failures=%d, total_duration=%.2fs",
            result.success_count,
            result.failure_count,
            result.metadata.get("total_duration", 0),
        )
        return result

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
        _LOGGER.debug("Shutting down report executor and closing provider connections")
        await self._provider_resolver.close_all()
        _LOGGER.debug("Report executor shutdown complete")

    def _get_report(self, report_id: str) -> ReportConfig:
        """Retrieve report configuration."""
        _LOGGER.debug("Retrieving report configuration for: %s", report_id)
        report = self._settings.reports.get(report_id)
        if report is None:
            _LOGGER.error("Report '%s' not found in configuration", report_id)
            raise KeyError(f"Report '{report_id}' not found")
        return report

    async def _execute_components(
        self,
        report: ReportConfig,
    ) -> List[ComponentExecutionResult]:
        """Execute all report components in parallel."""
        component_count = len(report.components)
        _LOGGER.info("Executing %d component(s) in parallel", component_count)
        tasks = [self._component_executor.execute(component) for component in report.components]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r.is_success)
        _LOGGER.info(
            "Component execution completed: %d/%d successful",
            success_count,
            component_count,
        )
        return results

    async def _render_report(
        self,
        report: ReportConfig,
        components: List[ComponentExecutionResult],
    ) -> str:
        """Render the full report HTML."""
        _LOGGER.debug("Building template context for report: %s", report.title)
        component_payloads = self._build_component_payloads(components)
        context = {
            "report": report,
            "generated_at": datetime.now(tz=timezone.utc),
            "components": component_payloads,
        }
        _LOGGER.debug("Rendering report template: %s", report.template)
        html = await self._template_engine.render(report, context)
        _LOGGER.debug("Report template rendered successfully")
        return html

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

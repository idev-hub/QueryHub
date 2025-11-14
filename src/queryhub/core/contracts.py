"""Core contracts used to decouple QueryHub components."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TYPE_CHECKING

from ..config.models import ComponentRenderConfig, ReportConfig, ReportEmailConfig, Settings

if TYPE_CHECKING:  # pragma: no cover - import guard
    from ..providers.base_query_provider import BaseQueryProvider
    from ..rendering.renderers import ComponentRenderer
    from ..services.executor import ReportExecutionResult


class ConfigLoaderProtocol(Protocol):
    """Abstraction for loading runtime settings."""

    async def load(self) -> Settings:
        """Load settings asynchronously."""


class ProviderFactoryProtocol(Protocol):
    """Create concrete providers using an identifier."""

    def create(self, provider_id: str) -> "BaseQueryProvider":
        """Return a provider configured for the requested id."""


class RendererResolverProtocol(Protocol):
    """Resolve renderers for a component definition."""

    def resolve(self, render_config: ComponentRenderConfig) -> "ComponentRenderer":
        """Return a renderer that can handle the config."""


class ReportTemplateEngine(Protocol):
    """Render the full HTML report using templating backend."""

    async def render(self, report: ReportConfig, context: Mapping[str, Any]) -> str:
        """Produce HTML for the given report/configuration context."""


class EmailSenderProtocol(Protocol):
    """Send report execution results via email."""

    async def send_report(
        self,
        result: "ReportExecutionResult",
        *,
        overrides: ReportEmailConfig | None = None,
    ) -> None:
        """Deliver the report result using optional overrides."""

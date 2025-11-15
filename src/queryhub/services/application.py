"""Application builder that wires QueryHub dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from ..config import ConfigLoader
from ..config.provider_models import ProviderConfig
from ..core.contracts import (
    ConfigLoaderProtocol,
    ProviderFactoryProtocol,
    RendererResolverProtocol,
    ReportTemplateEngine,
)
from ..core.providers import DefaultProviderFactory
from ..rendering.jinja_env import build_environment
from ..rendering.renderers import RendererRegistry, create_default_renderer_registry
from ..rendering.template_engine import JinjaReportTemplateEngine
from .executor import ReportExecutor


class QueryHubApplicationBuilder:
    """Composition root that assembles a SOLID-friendly executor instance."""

    def __init__(
        self,
        *,
        config_dir: Path,
        templates_dir: Path,
        auto_reload_templates: bool = False,
        email_mode: bool = False,
        config_loader: ConfigLoaderProtocol | None = None,
        provider_factory: ProviderFactoryProtocol | None = None,
        renderer_resolver: RendererResolverProtocol | None = None,
        template_engine: ReportTemplateEngine | None = None,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._templates_dir = Path(templates_dir)
        self._auto_reload_templates = auto_reload_templates
        self._email_mode = email_mode
        self._config_loader = config_loader
        self._provider_factory = provider_factory
        self._renderer_resolver = renderer_resolver
        self._template_engine = template_engine

    async def create_executor(self) -> ReportExecutor:
        settings = await self._resolve_loader().load()
        provider_factory = self._provider_factory or self._build_provider_factory(
            settings.providers, settings.credential_registry
        )
        renderer_resolver = self._renderer_resolver or self._build_renderer_resolver()
        template_engine = self._template_engine or self._build_template_engine()
        return ReportExecutor(
            settings,
            provider_factory=provider_factory,
            renderer_resolver=renderer_resolver,
            template_engine=template_engine,
        )

    def _resolve_loader(self) -> ConfigLoaderProtocol:
        return self._config_loader or ConfigLoader(self._config_dir)

    def _build_provider_factory(
        self, provider_configs: Mapping[str, ProviderConfig], credential_registry
    ):
        return DefaultProviderFactory(provider_configs, credential_registry)

    def _build_renderer_resolver(self) -> RendererRegistry:
        if isinstance(self._renderer_resolver, RendererRegistry):
            return self._renderer_resolver
        return create_default_renderer_registry(email_mode=self._email_mode)

    def _build_template_engine(self) -> ReportTemplateEngine:
        environment = build_environment(
            self._templates_dir, auto_reload=self._auto_reload_templates
        )
        return JinjaReportTemplateEngine(environment)

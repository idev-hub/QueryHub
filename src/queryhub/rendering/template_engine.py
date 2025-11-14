"""Template engine implementations for report rendering."""

from __future__ import annotations

from typing import Any, Mapping

from jinja2 import Environment

from ..config.models import ReportConfig
from ..core.contracts import ReportTemplateEngine


class JinjaReportTemplateEngine(ReportTemplateEngine):
    """Render reports using a configured Jinja2 environment."""

    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    async def render(self, report: ReportConfig, context: Mapping[str, Any]) -> str:
        template = self._environment.get_template(report.template)
        return await template.render_async(context)

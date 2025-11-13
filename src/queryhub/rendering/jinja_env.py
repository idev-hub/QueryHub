"""Jinja environment utilities."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def build_environment(templates_dir: Path, *, auto_reload: bool = False) -> Environment:
    """Create a configured Jinja2 environment."""

    loader = FileSystemLoader(str(templates_dir))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        enable_async=True,
        auto_reload=auto_reload,
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env

"""Backward-compatible wrapper for provider factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from ..config.models import ProviderConfig
from .base import QueryProvider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..core.providers import ProviderRegistry


class ProviderFactory:
    """Instantiate providers keyed by configuration entries (legacy wrapper)."""

    def __init__(
        self,
        provider_configs: Dict[str, ProviderConfig],
        registry: "ProviderRegistry" | None = None,
    ) -> None:
        from ..core.providers import DefaultProviderFactory, build_default_provider_registry

        self._factory = DefaultProviderFactory(
            provider_configs,
            registry or build_default_provider_registry(),
        )

    def create(self, provider_id: str) -> QueryProvider:
        return self._factory.create(provider_id)

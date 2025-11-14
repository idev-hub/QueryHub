"""Provider registry and factory implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping

from ..config.models import ProviderConfig, ProviderType
from ..core.errors import ProviderNotFoundError
from ..providers.adx import ADXQueryProvider
from ..providers.base import QueryProvider
from ..providers.csv import CSVQueryProvider
from ..providers.rest import RESTQueryProvider
from ..providers.sql import SQLQueryProvider
from .contracts import ProviderFactoryProtocol

ProviderConstructor = Callable[[ProviderConfig], QueryProvider]


class ProviderRegistry:
    """Mutable registry that maps provider types to constructors."""

    def __init__(self, mapping: Mapping[ProviderType, ProviderConstructor] | None = None) -> None:
        self._mapping: Dict[ProviderType, ProviderConstructor] = dict(mapping or {})

    def register(self, provider_type: ProviderType, constructor: ProviderConstructor) -> None:
        """Register a provider constructor for a type."""
        self._mapping[provider_type] = constructor

    def resolve(self, provider_type: ProviderType) -> ProviderConstructor:
        """Resolve a provider constructor by type."""
        try:
            return self._mapping[provider_type]
        except KeyError as exc:
            raise ProviderNotFoundError(
                f"No provider registered for type {provider_type!r}"
            ) from exc


def build_default_provider_registry() -> ProviderRegistry:
    """Return a registry pre-populated with built-in providers."""

    registry = ProviderRegistry()
    registry.register(ProviderType.ADX, ADXQueryProvider)  # type: ignore[arg-type]
    registry.register(ProviderType.SQL, SQLQueryProvider)  # type: ignore[arg-type]
    registry.register(ProviderType.REST, RESTQueryProvider)  # type: ignore[arg-type]
    registry.register(ProviderType.CSV, CSVQueryProvider)  # type: ignore[arg-type]
    return registry


@dataclass(slots=True)
class DefaultProviderFactory(ProviderFactoryProtocol):
    """Create providers using configuration and a registry."""

    provider_configs: Mapping[str, ProviderConfig]
    registry: ProviderRegistry

    def create(self, provider_id: str) -> QueryProvider:
        """Create a provider instance by ID."""
        config = self.provider_configs.get(provider_id)
        if config is None:
            raise ProviderNotFoundError(f"Provider '{provider_id}' is not defined")
        constructor = self.registry.resolve(config.type)
        return constructor(config)

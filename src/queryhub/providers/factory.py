"""Factory methods for provider instances."""

from __future__ import annotations

from typing import Dict

from ..config.models import ProviderConfig, ProviderType
from .adx import ADXQueryProvider
from .base import QueryProvider
from .csv import CSVQueryProvider
from .rest import RESTQueryProvider
from .sql import SQLQueryProvider


class ProviderFactory:
    """Instantiate providers keyed by configuration entries."""

    _registry = {
        ProviderType.ADX: ADXQueryProvider,
        ProviderType.SQL: SQLQueryProvider,
        ProviderType.REST: RESTQueryProvider,
        ProviderType.CSV: CSVQueryProvider,
    }

    def __init__(self, provider_configs: Dict[str, ProviderConfig]) -> None:
        self._configs = provider_configs

    def create(self, provider_id: str) -> QueryProvider:
        config = self._configs.get(provider_id)
        if config is None:
            raise KeyError(f"Provider '{provider_id}' is not defined")

        provider_cls = self._registry.get(config.type)
        if provider_cls is None:
            raise KeyError(f"No provider registered for type {config.type!r}")
        return provider_cls(config)

"""Provider abstractions for executing queries."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

from ..config.models import BaseProviderConfig


class ProviderExecutionError(RuntimeError):
    """Raised when a provider fails to execute a query."""


@dataclass(slots=True)
class QueryResult:
    """Normalized output returned by providers."""

    data: Any
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    mime_type: str | None = None


class QueryProvider(abc.ABC):
    """Abstract interface implemented by all providers."""

    def __init__(self, config: BaseProviderConfig) -> None:
        self._config = config

    @property
    def config(self) -> BaseProviderConfig:
        """Return provider configuration."""

        return self._config

    @abc.abstractmethod
    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute a provider-specific query and return normalised results."""

    async def close(self) -> None:
        """Override to release resources such as connection pools."""

    def _raise_missing_dependency(self, package: str, extras: str | None = None) -> None:
        suffix = f" Install the '{extras}' extra." if extras else ""
        raise ProviderExecutionError(
            f"Missing runtime dependency '{package}' required for {self.__class__.__name__}.{suffix}"
        )

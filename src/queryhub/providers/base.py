"""Provider abstractions for executing queries."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

from ..config.models import BaseProviderConfig
from ..core.errors import ProviderExecutionError, ProviderInitializationError


@dataclass(slots=True, frozen=True)
class QueryResult:
    """Normalized output returned by providers (immutable)."""

    data: Any
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    mime_type: str | None = None

    def with_metadata(self, **kwargs: Any) -> QueryResult:
        """Create a new result with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return QueryResult(data=self.data, metadata=new_metadata, mime_type=self.mime_type)


class QueryProvider(abc.ABC):
    """Abstract interface implemented by all providers following SRP."""

    def __init__(self, config: BaseProviderConfig) -> None:
        self._config = config
        self._validate_config()

    @property
    def config(self) -> BaseProviderConfig:
        """Return provider configuration."""
        return self._config

    @abc.abstractmethod
    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute a provider-specific query and return normalised results."""

    async def close(self) -> None:
        """Override to release resources such as connection pools."""

    def _validate_config(self) -> None:
        """Override to validate provider-specific configuration."""

    def _raise_missing_dependency(self, package: str, extras: str | None = None) -> None:
        """Raise a standardized error for missing dependencies."""
        suffix = f" Install the '{extras}' extra." if extras else ""
        raise ProviderInitializationError(
            f"Missing runtime dependency '{package}' required for {self.__class__.__name__}.{suffix}"
        )

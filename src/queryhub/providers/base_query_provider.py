"""Base query provider abstraction for all resource types.

This module defines the core abstractions for query execution across
all resource types (databases, REST APIs, file systems, cloud storage).

The design follows SOLID principles:
- Single Responsibility: Each provider handles one resource type
- Open/Closed: Easy to add new providers without modifying existing code
- Liskov Substitution: All providers implement the same interface
- Interface Segregation: Minimal interface with only essential methods
- Dependency Inversion: Application code depends on abstractions
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping, Optional

if TYPE_CHECKING:
    from ..config.models import ProviderConfig
    from ..core.credentials import CredentialRegistry

from ..core.errors import ProviderInitializationError


@dataclass(slots=True, frozen=True)
class QueryResult:
    """Immutable result from a query execution.

    This is the standard return type for all providers, ensuring consistency
    across different resource types.

    Attributes:
        data: The query result data (list of dicts, JSON, text, etc.)
        metadata: Provider-specific metadata (execution time, row count, etc.)
        mime_type: Optional MIME type for the data (useful for REST providers)
    """

    data: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    mime_type: Optional[str] = None


class BaseQueryProvider(ABC):
    """Abstract base class for all query provider implementations.

    This is the core abstraction that all providers must implement.
    It provides a unified interface for executing queries regardless
    of the underlying resource type.

    Design principles:
    - Resource-agnostic: Works with any queryable resource
    - Credential-injected: Receives credentials via dependency injection
    - Minimal coupling: Only depends on abstractions
    - Consistent interface: All providers work the same way

    The provider is responsible for:
    1. Connecting to the resource (using credentials)
    2. Executing queries
    3. Returning results in a standard format
    4. Proper resource cleanup
    """

    def __init__(
        self,
        config: ProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration from YAML
            credential_registry: Registry for resolving credential references
        """
        self._config = config
        self._credential_registry = credential_registry

    @property
    def config(self) -> ProviderConfig:
        """Get the provider configuration."""
        return self._config

    @property
    def credential_registry(self) -> Optional[CredentialRegistry]:
        """Get the credential registry."""
        return self._credential_registry

    @abstractmethod
    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute a query against the resource.

        This is the single responsibility of a provider: execute queries.
        The query format is provider-specific but always passed as a dict.

        Args:
            query: Query specification (format varies by provider)
                  Examples:
                  - ADX: {"text": "Users | take 10"}
                  - SQL: {"text": "SELECT * FROM users LIMIT 10"}
                  - REST: {"method": "GET", "endpoint": "/users"}
                  - CSV: {"path": "users.csv"}

        Returns:
            QueryResult with data and metadata

        Raises:
            ProviderExecutionError: If query execution fails
        """
        ...

    async def close(self) -> None:
        """Close connections and clean up resources.

        Override this to properly clean up any resources held by the provider
        (connections, clients, file handles, etc.).

        Default implementation does nothing.
        """
        pass

    async def __aenter__(self) -> BaseQueryProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - ensures cleanup."""
        await self.close()

    def _raise_missing_dependency(
        self,
        package: str,
        extras: Optional[str] = None,
    ) -> None:
        """Raise a helpful error about missing dependencies.

        Args:
            package: The missing package name
            extras: Optional extras group to install
        """
        if extras:
            install_cmd = f"pip install queryhub[{extras}]"
        else:
            install_cmd = f"pip install {package}"

        raise ProviderInitializationError(
            f"The '{package}' package is required for this provider. Install it with: {install_cmd}"
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(id={self.config.id})"

"""Base credential abstraction for all cloud providers.

This module defines the core abstractions for credential management across
all cloud providers (Azure, AWS, GCP) and resource types (databases, storage, APIs).

The design follows SOLID principles:
- Single Responsibility: Each credential handles one auth method
- Open/Closed: Easy to add new credential types without modifying existing code
- Liskov Substitution: All credentials implement the same interface
- Interface Segregation: Minimal interface with only essential methods
- Dependency Inversion: Providers depend on abstractions, not concrete implementations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

# Generic type for the configuration object
TConfig = TypeVar("TConfig")

# Generic type for the connection/client object returned by credentials
TConnection = TypeVar("TConnection")


class BaseCredential(ABC, Generic[TConfig, TConnection]):
    """Abstract base class for all credential implementations.

    This is the core abstraction that all credential strategies must implement.
    It provides a unified interface for obtaining authenticated connections
    regardless of the cloud provider or authentication method.

    Design principles:
    - Cloud-agnostic: Works with any cloud provider
    - Resource-agnostic: Can authenticate to any service (databases, storage, APIs)
    - Strategy pattern: Each credential type is a different strategy
    - Minimal interface: Only one core method to implement

    Type parameters:
        TConfig: The type of configuration this credential accepts
                Examples: AzureCredentialConfig, AWSCredentialConfig,
                GenericCredentialConfig
        TConnection: The type of connection/client object this credential creates
                    Examples: KustoConnectionStringBuilder, boto3.Session,
                    google.cloud.bigquery.Client, sqlalchemy.Engine
    """

    def __init__(self, config: TConfig | None = None) -> None:
        """Initialize credential with configuration.

        Args:
            config: Optional credential configuration from YAML
        """
        self.config = config

    @abstractmethod
    async def get_connection(self, **context: Any) -> TConnection:
        """Get authenticated connection/client for the target service.

        This is the single responsibility of a credential: provide authentication.
        The credential doesn't need to know what the connection will be used for,
        it just needs to authenticate properly.

        Args:
            **context: Service-specific context needed for authentication
                      Examples:
                      - Azure ADX: cluster_uri, database
                      - AWS S3: region_name, service_name
                      - GCP BigQuery: project_id, location
                      - SQL: No additional context needed

        Returns:
            Authenticated connection/client object ready to use

        Raises:
            CredentialError: If authentication fails
        """
        ...

    async def close(self) -> None:
        """Clean up any resources held by this credential.

        Override this if your credential maintains stateful resources
        (e.g., cached tokens, open sessions) that need cleanup.

        Default implementation does nothing (stateless credentials).
        """
        pass

    def __repr__(self) -> str:
        """String representation for debugging."""
        config_type = type(self.config).__name__ if self.config else "None"
        return f"{self.__class__.__name__}(config={config_type})"

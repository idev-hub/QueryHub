"""Provider factory for creating provider instances.

This factory creates providers and injects the credential registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.errors import ProviderNotFoundError
from .base_query_provider import BaseQueryProvider

if TYPE_CHECKING:
    from ..config.provider_models import ProviderConfig
    from ..core.credentials import CredentialRegistry


def create_provider(
    config: ProviderConfig,
    credential_registry: CredentialRegistry,
) -> BaseQueryProvider:
    """Factory function to create the appropriate provider instance.

    This is the single entry point for provider creation. It routes to
    the appropriate provider class based on the provider type.

    Args:
        config: Provider configuration from YAML
        credential_registry: Registry for resolving credential references

    Returns:
        Appropriate BaseQueryProvider instance

    Raises:
        ProviderNotFoundError: If provider type is unsupported
    """
    provider_type = config.type

    # Map provider types to their implementations
    provider_map = {
        "adx": ("azure.resources.adx", "ADXQueryProvider"),
        "sql": ("generic.resources.sql", "SQLQueryProvider"),
        "rest": ("generic.resources.rest", "RESTQueryProvider"),
        "csv": ("generic.resources.csv", "CSVQueryProvider"),
        # Future: s3, athena, bigquery, etc.
    }

    if provider_type not in provider_map:
        raise ProviderNotFoundError(
            f"Unsupported provider type: {provider_type}. "
            f"Supported types: {', '.join(provider_map.keys())}"
        )

    module_path, class_name = provider_map[provider_type]

    # Dynamic import to avoid circular dependencies
    if provider_type == "adx":
        from .azure.resources.adx import ADXQueryProvider

        return ADXQueryProvider(config, credential_registry)
    elif provider_type == "sql":
        from .generic.resources.sql import SQLQueryProvider

        return SQLQueryProvider(config, credential_registry)
    elif provider_type == "rest":
        from .generic.resources.rest import RESTQueryProvider

        return RESTQueryProvider(config, credential_registry)
    elif provider_type == "csv":
        from .generic.resources.csv import CSVQueryProvider

        return CSVQueryProvider(config, credential_registry)
    else:
        raise ProviderNotFoundError(f"Provider type '{provider_type}' not implemented yet")

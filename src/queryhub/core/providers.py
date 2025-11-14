"""Provider registry and factory implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..core.errors import ProviderNotFoundError
from ..providers.base_query_provider import BaseQueryProvider
from ..providers.provider_factory import create_provider
from .contracts import ProviderFactoryProtocol
from .credentials import CredentialRegistry


@dataclass(slots=True)
class DefaultProviderFactory(ProviderFactoryProtocol):
    """Create providers using configuration and credential registry."""

    provider_configs: Mapping[str, Any]  # Type-specific provider configs
    credential_registry: CredentialRegistry

    def create(self, provider_id: str) -> BaseQueryProvider:
        """Create a provider instance by ID.

        Args:
            provider_id: The provider identifier

        Returns:
            BaseQueryProvider instance with credentials injected

        Raises:
            ProviderNotFoundError: If provider ID not found
        """
        config = self.provider_configs.get(provider_id)
        if config is None:
            raise ProviderNotFoundError(f"Provider '{provider_id}' is not defined")

        # Use the new factory function that handles dependency injection
        return create_provider(config, self.credential_registry)

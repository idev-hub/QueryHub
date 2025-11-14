"""Credential registry and resolution for multi-cloud providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional

from ..config.models import CredentialConfig
from ..core.errors import ProviderInitializationError
from ..providers.base_credentials import BaseCredential
from ..providers.credential_factory import create_credential


@dataclass(slots=True)
class CredentialRegistry:
    """Registry for storing and resolving credentials by ID.

    This allows credentials to be defined once and reused across multiple
    providers, reducing duplication and making credential management easier.
    """

    _credentials: Dict[
        str, tuple[str, str, CredentialConfig]
    ]  # id -> (cloud_provider, type, config)
    _credential_cache: Dict[str, BaseCredential]  # id -> credential instance

    def __init__(
        self, credentials: Optional[Mapping[str, tuple[str, str, CredentialConfig]]] = None
    ) -> None:
        """Initialize the credential registry.

        Args:
            credentials: Optional initial mapping of credential ID to (cloud_provider, type, config)
        """
        self._credentials = dict(credentials or {})
        self._credential_cache = {}

    def register(
        self,
        credential_id: str,
        cloud_provider: str,
        credential_type: str,
        config: CredentialConfig,
    ) -> None:
        """Register a credential configuration by ID.

        Args:
            credential_id: Unique identifier for the credential
            cloud_provider: Cloud provider (azure, aws, gcp, generic, postgresql)
            credential_type: Type of credential (default_credentials, access_key, etc.)
            config: The credential configuration
        """
        self._credentials[credential_id] = (cloud_provider, credential_type, config)
        # Clear cache for this credential if it exists
        self._credential_cache.pop(credential_id, None)

    def get_credential(
        self,
        credential_ref: str,
        cloud_provider: Optional[str] = None,
    ) -> BaseCredential:
        """Get or create a credential instance by ID.

        This method caches credential instances for reuse.

        Args:
            credential_ref: Credential ID string
            cloud_provider: Optional cloud provider override (usually not needed)

        Returns:
            BaseCredential instance

        Raises:
            ProviderInitializationError: If credential ID not found
        """
        if not isinstance(credential_ref, str):
            raise ProviderInitializationError(
                f"Credential reference must be a string ID, got {type(credential_ref)}"
            )

        # Check cache first
        if credential_ref in self._credential_cache:
            return self._credential_cache[credential_ref]

        # Look up credential configuration
        if credential_ref not in self._credentials:
            raise ProviderInitializationError(
                f"Credential '{credential_ref}' not found in registry. "
                f"Available credentials: {', '.join(self._credentials.keys()) or 'none'}"
            )

        provider, cred_type, config = self._credentials[credential_ref]

        # Use override if provided
        if cloud_provider:
            provider = cloud_provider

        # Create credential instance
        credential = create_credential(config, provider, cred_type)

        # Cache for reuse
        self._credential_cache[credential_ref] = credential

        return credential

    def list_credential_ids(self) -> list[str]:
        """Get list of all registered credential IDs.

        Returns:
            List of credential IDs
        """
        return list(self._credentials.keys())

    def __len__(self) -> int:
        """Return the number of registered credentials."""
        return len(self._credentials)

    def __contains__(self, credential_id: str) -> bool:
        """Check if a credential ID is registered."""
        return credential_id in self._credentials

    async def close_all(self) -> None:
        """Close all cached credential instances."""
        for credential in self._credential_cache.values():
            await credential.close()
        self._credential_cache.clear()

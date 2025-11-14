"""Azure credential implementations.

This module contains all credential strategies for Azure services.
Each credential type represents a different authentication method that
works across all Azure services.
"""

from __future__ import annotations

from typing import Any

from ...config.credential_models import AzureCredentialConfig
from ...core.errors import ProviderInitializationError
from ..base_credentials import BaseCredential


class AzureDefaultCredential(BaseCredential[AzureCredentialConfig, Any]):
    """Azure DefaultAzureCredential - automatic credential discovery.

    Tries multiple authentication methods in order:
    1. Environment variables (service principal)
    2. Managed Identity (when in Azure)
    3. Azure CLI (local development)
    4. Azure PowerShell
    5. Interactive browser

    Works with: ADX, Storage, SQL, Service Bus, all Azure services
    """

    def __init__(self, config: AzureCredentialConfig | None = None) -> None:
        super().__init__(config)
        self._azure_credential: Any = None

    async def get_connection(self, **context: Any) -> Any:
        """Get connection using DefaultAzureCredential."""
        service_type = context.get("service_type", "kusto")

        if service_type == "kusto":
            return await self._get_kusto_connection(**context)
        else:
            raise ProviderInitializationError(
                f"Azure DefaultCredential does not support service_type='{service_type}'"
            )

    async def _get_kusto_connection(self, **context: Any) -> Any:
        """Get Kusto connection with DefaultAzureCredential."""
        try:
            from azure.identity.aio import DefaultAzureCredential as AzureDefaultCred
            from azure.kusto.data import KustoConnectionStringBuilder
        except ImportError as exc:
            raise ProviderInitializationError(
                "azure-identity and azure-kusto-data are required. "
                "Install with: pip install azure-identity azure-kusto-data"
            ) from exc

        cluster_uri = context.get("cluster_uri")
        if not cluster_uri:
            raise ProviderInitializationError("cluster_uri is required for Kusto")

        self._azure_credential = AzureDefaultCred()

        return KustoConnectionStringBuilder.with_aad_token_provider(  # type: ignore[attr-defined]
            cluster_uri,
            lambda: self._azure_credential.get_token("https://kusto.kusto.windows.net/.default"),
        )

    async def close(self) -> None:
        if self._azure_credential:
            await self._azure_credential.close()


class AzureManagedIdentityCredential(BaseCredential[AzureCredentialConfig, Any]):
    """Azure Managed Identity authentication.

    Uses the managed identity assigned to Azure resources (VMs, App Service, etc.)

    Works with: ADX, Storage, SQL, Service Bus, all Azure services
    """

    def __init__(self, config: AzureCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> Any:
        """Get connection using Managed Identity."""
        service_type = context.get("service_type", "kusto")

        if service_type == "kusto":
            return await self._get_kusto_connection(**context)
        else:
            raise ProviderInitializationError(
                f"Azure ManagedIdentity does not support service_type='{service_type}'"
            )

    async def _get_kusto_connection(self, **context: Any) -> Any:
        """Get Kusto connection with Managed Identity."""
        try:
            from azure.kusto.data import KustoConnectionStringBuilder
        except ImportError as exc:
            raise ProviderInitializationError(
                "azure-kusto-data is required. Install with: pip install azure-kusto-data"
            ) from exc

        cluster_uri = context.get("cluster_uri")
        if not cluster_uri:
            raise ProviderInitializationError("cluster_uri is required for Kusto")

        client_id = getattr(self.config, "client_id", None)

        return KustoConnectionStringBuilder.with_aad_managed_service_identity(  # type: ignore[attr-defined]
            cluster_uri, client_id=client_id
        )


class AzureServicePrincipalCredential(BaseCredential[AzureCredentialConfig, Any]):
    """Azure Service Principal authentication.

    Uses client_id, client_secret, and tenant_id for authentication.
    Best for CI/CD pipelines and automated scenarios.

    Works with: ADX, Storage, SQL, Service Bus, all Azure services
    """

    def __init__(self, config: AzureCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> Any:
        """Get connection using Service Principal."""
        service_type = context.get("service_type", "kusto")

        if service_type == "kusto":
            return await self._get_kusto_connection(**context)
        else:
            raise ProviderInitializationError(
                f"Azure ServicePrincipal does not support service_type='{service_type}'"
            )

    async def _get_kusto_connection(self, **context: Any) -> Any:
        """Get Kusto connection with Service Principal."""
        try:
            from azure.kusto.data import KustoConnectionStringBuilder
        except ImportError as exc:
            raise ProviderInitializationError(
                "azure-kusto-data is required. Install with: pip install azure-kusto-data"
            ) from exc

        cluster_uri = context.get("cluster_uri")
        if not cluster_uri:
            raise ProviderInitializationError("cluster_uri is required for Kusto")

        assert self.config is not None, "Config is required"
        assert self.config.client_id is not None, "client_id is required"
        assert self.config.client_secret is not None, "client_secret is required"
        assert self.config.tenant_id is not None, "tenant_id is required"

        return KustoConnectionStringBuilder.with_aad_application_key_authentication(
            cluster_uri,
            self.config.client_id,
            self.config.client_secret.get_secret_value(),
            self.config.tenant_id,
        )


class AzureTokenCredential(BaseCredential[AzureCredentialConfig, Any]):
    """Azure pre-acquired token authentication.

    Uses a pre-acquired access token for authentication.
    Useful when you manage token acquisition separately.

    Works with: ADX, Storage, SQL, Service Bus, all Azure services
    """

    def __init__(self, config: AzureCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> Any:
        """Get connection using pre-acquired token."""
        service_type = context.get("service_type", "kusto")

        if service_type == "kusto":
            return await self._get_kusto_connection(**context)
        else:
            raise ProviderInitializationError(
                f"Azure Token does not support service_type='{service_type}'"
            )

    async def _get_kusto_connection(self, **context: Any) -> Any:
        """Get Kusto connection with token."""
        try:
            from azure.kusto.data import KustoConnectionStringBuilder
        except ImportError as exc:
            raise ProviderInitializationError(
                "azure-kusto-data is required. Install with: pip install azure-kusto-data"
            ) from exc

        cluster_uri = context.get("cluster_uri")
        if not cluster_uri:
            raise ProviderInitializationError("cluster_uri is required for Kusto")

        assert self.config is not None, "Config is required"
        assert self.config.token is not None, "token is required"

        return KustoConnectionStringBuilder.with_aad_application_token_authentication(
            cluster_uri,
            self.config.token.get_secret_value(),
        )

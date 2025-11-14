"""Azure Data Explorer (Kusto) query provider.

This provider executes KQL (Kusto Query Language) queries against
Azure Data Explorer clusters.
"""

from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

from ....config.models import ADXProviderConfig
from ....core.credentials import CredentialRegistry
from ....core.errors import ProviderExecutionError, ProviderInitializationError
from ...base_credentials import BaseCredential
from ...base_query_provider import BaseQueryProvider, QueryResult


class ADXQueryProvider(BaseQueryProvider):
    """Execute Kusto queries against Azure Data Explorer.

    This provider is cloud-specific (Azure only) but credential-agnostic.
    It works with any Azure credential that can authenticate to ADX.
    """

    def __init__(
        self,
        config: ADXProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        super().__init__(config, credential_registry)
        self._credential: Optional[BaseCredential] = None
        self._client = None
        self._client_lock = asyncio.Lock()

    @property
    def config(self) -> ADXProviderConfig:
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute a KQL query.

        Args:
            query: Query specification with keys:
                  - text: KQL query string (required)
                  - client_request_id: Optional request ID
                  - parameters: Optional query parameters
                  - options: Optional Kusto client options
                  - timeout_seconds: Optional query timeout
        """
        client = await self._get_client()
        query_text = query.get("text")
        if not query_text:
            raise ProviderExecutionError("ADX queries require a 'text' entry")

        properties = self._build_client_properties(query)

        try:
            response = await client.execute(
                self.config.database,
                query_text,
                properties=properties,
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderExecutionError(f"ADX query failed: {exc}") from exc

        primary = response.primary_results[0] if response.primary_results else None
        rows = []
        if primary:
            for row in primary:
                rows.append(dict(row))

        metadata = {
            "execution_time": response.execution_time,
            "request_id": response.request_id,
        }
        return QueryResult(data=rows, metadata=metadata)

    async def close(self) -> None:
        """Close ADX client and credential resources."""
        if self._client is not None:
            await self._client.close()
        if self._credential is not None:
            await self._credential.close()

    async def _get_client(self):
        """Get or create ADX client (lazy initialization with thread safety)."""
        if self._client is not None:
            return self._client
        async with self._client_lock:
            if self._client is not None:
                return self._client
            self._client = await self._create_client()
        return self._client

    async def _create_client(self):
        """Create ADX client using credential from registry."""
        try:
            from azure.kusto.data.aio import KustoClient
        except ImportError as exc:
            self._raise_missing_dependency("azure-kusto-data", extras="adx")
            raise ProviderInitializationError("Azure Kusto dependency missing") from exc

        if not self.credential_registry:
            raise ProviderInitializationError("Credential registry is required")

        # Get credential from registry
        self._credential = self.credential_registry.get_credential(
            self.config.credentials, cloud_provider="azure"
        )

        # Get authenticated connection (KustoConnectionStringBuilder)
        kcsb = await self._credential.get_connection(
            service_type="kusto", cluster_uri=self.config.cluster_uri, database=self.config.database
        )

        return KustoClient(kcsb)

    def _build_client_properties(self, query: Mapping[str, Any]):
        """Build Kusto client request properties from query."""
        try:
            from azure.kusto.data import ClientRequestProperties
        except ImportError:
            self._raise_missing_dependency("azure-kusto-data", extras="adx")

        properties = ClientRequestProperties()

        if client_request_id := query.get("client_request_id"):
            prefix = self.config.client_request_id_prefix or "queryhub"
            properties.client_request_id = f"{prefix};{client_request_id}"

        for name, value in query.get("parameters", {}).items():
            properties.set_parameter(name, value)

        timeout = query.get("timeout_seconds") or self.config.default_timeout_seconds
        if timeout:
            properties.set_option("servertimeout", f"{timeout}s")

        for option_name, option_value in query.get("options", {}).items():
            properties.set_option(option_name, option_value)

        return properties

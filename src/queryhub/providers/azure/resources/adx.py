"""Azure Data Explorer (Kusto) query provider.

This provider executes KQL (Kusto Query Language) queries against
Azure Data Explorer clusters.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping, Optional

from ....config.provider_models import ProviderConfig
from ....core.credentials import CredentialRegistry
from ....core.errors import ProviderExecutionError, ProviderInitializationError
from ...base_credentials import BaseCredential
from ...base_query_provider import BaseQueryProvider, QueryResult

_LOGGER = logging.getLogger(__name__)


class ADXQueryProvider(BaseQueryProvider):
    """Execute Kusto queries against Azure Data Explorer.

    This provider is cloud-specific (Azure only) but credential-agnostic.
    It works with any Azure credential that can authenticate to ADX.
    """

    def __init__(
        self,
        config: ProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        super().__init__(config, credential_registry)
        if config.type != "adx" or not config.resource.adx:
            raise ProviderInitializationError("ADXQueryProvider requires adx resource configuration")
        self._credential: Optional[BaseCredential] = None
        self._client = None
        self._client_lock = asyncio.Lock()
        _LOGGER.info(
            "ADX provider initialized: cluster=%s, database=%s",
            self.adx_config.cluster_uri,
            self.adx_config.database,
        )

    @property
    def adx_config(self):
        """Get ADX-specific configuration from resource."""
        return self.config.resource.adx

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

        _LOGGER.debug("Executing ADX query on database: %s", self.adx_config.database)
        _LOGGER.debug("Query text (first 100 chars): %s", query_text[:100])
        properties = self._build_client_properties(query)

        try:
            response = await client.execute(
                self.adx_config.database,
                query_text,
                properties=properties,
            )
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("ADX query failed: %s", exc, exc_info=True)
            raise ProviderExecutionError(f"ADX query failed: {exc}") from exc

        primary = response.primary_results[0] if response.primary_results else None
        rows = []
        if primary:
            for row in primary:
                rows.append(dict(row))

        _LOGGER.debug(
            "ADX query completed: %d row(s), execution_time=%s",
            len(rows),
            response.execution_time,
        )
        metadata = {
            "execution_time": response.execution_time,
            "request_id": response.request_id,
        }
        return QueryResult(data=rows, metadata=metadata)

    async def close(self) -> None:
        """Close ADX client and credential resources."""
        _LOGGER.debug("Closing ADX provider connections")
        if self._client is not None:
            await self._client.close()
            _LOGGER.debug("ADX client closed")
        if self._credential is not None:
            await self._credential.close()
            _LOGGER.debug("ADX credentials closed")

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
        _LOGGER.debug("Creating ADX client for cluster: %s", self.adx_config.cluster_uri)
        try:
            from azure.kusto.data.aio import KustoClient
        except ImportError as exc:
            self._raise_missing_dependency("azure-kusto-data", extras="adx")
            raise ProviderInitializationError("Azure Kusto dependency missing") from exc

        if not self.credential_registry:
            raise ProviderInitializationError("Credential registry is required")

        # Get credential from registry
        _LOGGER.debug("Retrieving Azure credentials: %s", self.config.credentials)
        self._credential = self.credential_registry.get_credential(
            self.config.credentials, cloud_provider="azure"
        )

        # Get authenticated connection (KustoConnectionStringBuilder)
        _LOGGER.debug("Establishing authenticated connection to ADX")
        kcsb = await self._credential.get_connection(
            service_type="kusto", cluster_uri=self.adx_config.cluster_uri, database=self.adx_config.database
        )

        client = KustoClient(kcsb)
        _LOGGER.info("ADX client created successfully")
        return client

    def _build_client_properties(self, query: Mapping[str, Any]):
        """Build Kusto client request properties from query."""
        try:
            from azure.kusto.data import ClientRequestProperties
        except ImportError:
            self._raise_missing_dependency("azure-kusto-data", extras="adx")

        properties = ClientRequestProperties()

        if client_request_id := query.get("client_request_id"):
            prefix = self.adx_config.client_request_id_prefix or "queryhub"
            properties.client_request_id = f"{prefix};{client_request_id}"

        for name, value in query.get("parameters", {}).items():
            properties.set_parameter(name, value)

        timeout = query.get("timeout_seconds") or self.config.default_timeout_seconds
        if timeout:
            properties.set_option("servertimeout", f"{timeout}s")

        for option_name, option_value in query.get("options", {}).items():
            properties.set_option(option_name, option_value)

        return properties

"""Azure Data Explorer provider implementation."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from ..config.models import ADXProviderConfig, CredentialType, ManagedIdentityCredential
from ..core.errors import ProviderExecutionError, ProviderInitializationError
from .base import QueryProvider, QueryResult


class ADXQueryProvider(QueryProvider):
    """Execute Kusto queries against Azure Data Explorer."""

    def __init__(self, config: ADXProviderConfig) -> None:
        super().__init__(config)
        self._client = None
        self._client_lock = asyncio.Lock()

    @property
    def config(self) -> ADXProviderConfig:
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
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
        client = self._client
        if client is not None:
            await client.close()

    async def _get_client(self):
        if self._client is not None:
            return self._client
        async with self._client_lock:
            if self._client is not None:
                return self._client
            self._client = await self._create_client()
        return self._client

    async def _create_client(self):
        try:
            from azure.kusto.data import KustoConnectionStringBuilder
            from azure.kusto.data.aio import KustoClient
        except ImportError as exc:
            self._raise_missing_dependency("azure-kusto-data", extras="adx")
            raise ProviderInitializationError("Azure Kusto dependency missing") from exc

        credential = self.config.credentials
        cluster_uri = self.config.cluster_uri
        builder = None

        if credential is None or credential.type is CredentialType.NONE:
            builder = KustoConnectionStringBuilder.with_aad_device_authentication(cluster_uri)
        elif credential.type is CredentialType.MANAGED_IDENTITY:
            cred = credential
            assert isinstance(cred, ManagedIdentityCredential)
            builder = KustoConnectionStringBuilder.with_aad_managed_service_identity(
                cluster_uri, client_id=cred.client_id
            )
        elif credential.type is CredentialType.SERVICE_PRINCIPAL:
            builder = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                cluster_uri,
                credential.client_id,
                credential.client_secret.get_secret_value(),
                credential.tenant_id,
            )
        elif credential.type is CredentialType.USERNAME_PASSWORD:
            builder = KustoConnectionStringBuilder.with_aad_device_authentication(cluster_uri)
            builder.username = credential.username
            builder.password = credential.password.get_secret_value()
        elif credential.type is CredentialType.CONNECTION_STRING:
            builder = KustoConnectionStringBuilder.from_connection_string(
                credential.connection_string.get_secret_value()
            )
        elif credential.type is CredentialType.TOKEN:
            builder = KustoConnectionStringBuilder.with_aad_application_token_authentication(
                cluster_uri,
                credential.token.get_secret_value(),
            )
        else:
            raise ProviderExecutionError(f"Unsupported credential type {credential.type}")

        builder.set_option("azure_ad_endpoint", "https://login.microsoftonline.com")
        return KustoClient(builder)

    def _build_client_properties(self, query: Mapping[str, Any]):
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

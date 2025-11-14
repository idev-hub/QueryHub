"""REST API query provider.

This provider executes HTTP requests against REST APIs using aiohttp.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Mapping, Optional
from urllib.parse import urljoin

from ....config.models import RESTProviderConfig
from ....core.credentials import CredentialRegistry
from ....core.errors import ProviderExecutionError
from ...base_credentials import BaseCredential
from ...base_query_provider import BaseQueryProvider, QueryResult


class RESTQueryProvider(BaseQueryProvider):
    """Execute HTTP requests against REST endpoints.

    This provider is cloud-agnostic and works with any REST API.
    """

    def __init__(
        self,
        config: RESTProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        super().__init__(config, credential_registry)
        self._credential: Optional[BaseCredential] = None
        self._session = None
        self._session_lock = asyncio.Lock()

    @property
    def config(self) -> RESTProviderConfig:
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute an HTTP request.

        Args:
            query: Query specification with keys:
                  - method: HTTP method (GET, POST, etc.)
                  - endpoint or path: API endpoint path
                  - url: Full URL (overrides base_url + endpoint)
                  - headers: Optional request headers
                  - params: Optional query parameters
                  - json: Optional JSON body
                  - data: Optional form data
                  - timeout_seconds: Optional request timeout
        """
        session = await self._get_session()
        method = str(query.get("method", "GET")).upper()
        endpoint = query.get("endpoint") or query.get("path")
        url = query.get("url")

        if not url:
            if not endpoint:
                raise ProviderExecutionError("REST queries require an 'endpoint' or 'url'")
            url = urljoin(self.config.base_url.rstrip("/") + "/", str(endpoint).lstrip("/"))

        headers = {**self.config.default_headers, **query.get("headers", {})}

        # Add authentication headers from credential
        auth_header = await self._build_auth_header()
        headers.update(auth_header)

        timeout_seconds = query.get("timeout_seconds") or self.config.default_timeout_seconds
        params = query.get("params")
        json_payload = query.get("json")
        data_payload = query.get("data")

        try:
            import aiohttp
        except ImportError as exc:
            self._raise_missing_dependency("aiohttp")
            raise ProviderExecutionError("aiohttp dependency missing") from exc

        timeout = aiohttp.ClientTimeout(total=timeout_seconds) if timeout_seconds else None
        request_options = dict(self.config.request_options)
        request_options.update(query.get("request_options", {}))

        async with session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_payload,
            data=data_payload,
            timeout=timeout,
            **request_options,
        ) as response:
            content_type = response.headers.get("Content-Type", "").split(";")[0]

            if response.status >= 400:
                body = await response.text()
                raise ProviderExecutionError(
                    f"REST request failed with status {response.status}: {body[:200]}"
                )

            if content_type == "application/json":
                payload = await response.json()
            else:
                payload = await response.text()

            metadata = {
                "status": response.status,
                "url": str(response.url),
                "headers": dict(response.headers),
            }
            return QueryResult(data=payload, metadata=metadata, mime_type=content_type)

    async def close(self) -> None:
        """Close HTTP session and credential resources."""
        if self._session is not None:
            await self._session.close()
        if self._credential is not None:
            await self._credential.close()

    async def _get_session(self):
        """Get or create HTTP session (lazy initialization with thread safety)."""
        if self._session is not None:
            return self._session
        async with self._session_lock:
            if self._session is None:
                self._session = await self._create_session()
        return self._session

    async def _create_session(self):
        """Create aiohttp session."""
        try:
            import aiohttp
        except ImportError as exc:
            self._raise_missing_dependency("aiohttp")
            raise ProviderExecutionError("aiohttp dependency missing") from exc

        timeout = aiohttp.ClientTimeout(total=self.config.default_timeout_seconds)
        session = aiohttp.ClientSession(timeout=timeout, headers=self.config.default_headers)
        return session

    async def _build_auth_header(self) -> dict[str, str]:
        """Build authentication header from credential."""
        if not self.credential_registry or not self.config.credentials:
            return {}

        # credentials can be a string ID or a credential config (legacy)
        if isinstance(self.config.credentials, str):
            cred_id = self.config.credentials
        else:
            # Legacy: credentials is a config object, not supported with registry
            raise ValueError("Credential configs not supported with registry")
        self._credential = self.credential_registry.get_credential(
            cred_id,
            cloud_provider="generic",
        )
        cred_data = await self._credential.get_connection()

        if not cred_data:
            return {}

        # Token-based auth
        if isinstance(cred_data, dict) and "token" in cred_data:
            token_value = cred_data["token"]
            template = cred_data.get("template", "Bearer {token}")
            header_name = cred_data.get("header_name", "Authorization")
            return {header_name: template.format(token=token_value)}

        # Username/password (Basic Auth)
        if isinstance(cred_data, dict) and "username" in cred_data:
            username = cred_data["username"]
            password = cred_data["password"]
            token = f"{username}:{password}"
            encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}

        return {}

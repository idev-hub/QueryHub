"""Asynchronous REST provider implemented with aiohttp."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping
from urllib.parse import urljoin

from ..config.models import CredentialType, RESTProviderConfig, TokenCredential
from .base import ProviderExecutionError, QueryProvider, QueryResult


class RESTQueryProvider(QueryProvider):
    """Execute HTTP requests against REST endpoints."""

    def __init__(self, config: RESTProviderConfig) -> None:
        super().__init__(config)
        self._session = None
        self._session_lock = asyncio.Lock()

    @property
    def config(self) -> RESTProviderConfig:  # type: ignore[override]
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        session = await self._get_session()
        method = str(query.get("method", "GET")).upper()
        endpoint = query.get("endpoint") or query.get("path")
        url = query.get("url")
        if not url:
            if not endpoint:
                raise ProviderExecutionError("REST queries require an 'endpoint' or 'url'")
            url = urljoin(self.config.base_url.rstrip("/") + "/", str(endpoint).lstrip("/"))

        headers = {**self.config.default_headers, **query.get("headers", {})}
        auth_header = self._build_auth_header()
        headers.update(auth_header)

        timeout_seconds = query.get("timeout_seconds") or self.config.default_timeout_seconds

        params = query.get("params")
        json_payload = query.get("json")
        data_payload = query.get("data")

        try:
            import aiohttp
        except ImportError as exc:  # pragma: no cover - import guard
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
        session = self._session
        if session is not None:
            await session.close()

    async def _get_session(self):
        if self._session is not None:
            return self._session
        async with self._session_lock:
            if self._session is None:
                self._session = await self._create_session()
        return self._session

    async def _create_session(self):
        try:
            import aiohttp
        except ImportError as exc:  # pragma: no cover - import guard
            self._raise_missing_dependency("aiohttp")
            raise ProviderExecutionError("aiohttp dependency missing") from exc

        timeout = aiohttp.ClientTimeout(total=self.config.default_timeout_seconds)
        session = aiohttp.ClientSession(timeout=timeout, headers=self.config.default_headers)
        return session

    def _build_auth_header(self) -> dict[str, str]:
        credential = self.config.credentials
        if credential and credential.type is CredentialType.TOKEN:
            assert isinstance(credential, TokenCredential)
            token_value = credential.token.get_secret_value()
            template = credential.template or "{token}"
            header_name = credential.header_name or "Authorization"
            return {header_name: template.format(token=token_value)}
        if (
            credential
            and credential.type is CredentialType.USERNAME_PASSWORD
            and credential.username
            and credential.password
        ):
            import base64

            token = f"{credential.username}:{credential.password.get_secret_value()}"
            encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        return {}

"""Async SQL provider backed by SQLAlchemy."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from ..config.models import (
    CredentialType,
    SQLProviderConfig,
    SQLProviderTarget,
    UsernamePasswordCredential,
)
from .base import ProviderExecutionError, QueryProvider, QueryResult


class SQLQueryProvider(QueryProvider):
    """Run SQL statements using SQLAlchemy's asyncio support."""

    def __init__(self, config: SQLProviderConfig) -> None:
        super().__init__(config)
        self._engine: AsyncEngine | None = None
        self._engine_lock = asyncio.Lock()
        self._sessionmaker: async_sessionmaker | None = None

    @property
    def config(self) -> SQLProviderConfig:  # type: ignore[override]
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        statement_text = query.get("text")
        if not statement_text:
            raise ProviderExecutionError("SQL queries require a 'text' entry")

        timeout = query.get("timeout_seconds") or self.config.default_timeout_seconds
        params = query.get("parameters", {})

        try:
            engine = await self._get_engine()
            async with engine.connect() as connection:
                if timeout:
                    connection = await connection.execution_options(timeout=timeout)
                statement = text(statement_text)
                result = await connection.execute(statement, params)
                records = [dict(row) for row in result.mappings().all()]
        except SQLAlchemyError as exc:
            raise ProviderExecutionError(f"SQL execution failed: {exc}") from exc

        metadata = {"rowcount": len(records)}
        return QueryResult(data=records, metadata=metadata)

    async def close(self) -> None:
        engine = self._engine
        if engine is not None:
            await engine.dispose()

    async def _get_engine(self) -> AsyncEngine:
        if self._engine is not None:
            return self._engine
        async with self._engine_lock:
            if self._engine is None:
                self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> AsyncEngine:
        target = self.config.target
        credentials = self.config.credentials
        connect_args: dict[str, Any] = dict(target.options)

        url = self._build_url(target, credentials)

        if credentials and credentials.type is CredentialType.TOKEN:
            connect_args.setdefault("access_token", credentials.token.get_secret_value())

        engine = create_async_engine(
            url,
            echo=self.config.metadata.get("echo", False),
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        self._sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
        return engine

    def _build_url(self, target: SQLProviderTarget, credentials):
        if credentials and credentials.type is CredentialType.CONNECTION_STRING:
            return credentials.connection_string.get_secret_value()
        if target.dsn:
            return target.dsn

        driver = target.driver or "postgresql+asyncpg"
        username = None
        password = None

        if isinstance(credentials, UsernamePasswordCredential):
            username = credentials.username
            password = credentials.password.get_secret_value()
        elif credentials and credentials.type is CredentialType.SERVICE_PRINCIPAL:
            username = credentials.client_id
            password = credentials.client_secret.get_secret_value()

        url = URL.create(
            drivername=driver,
            username=username,
            password=password,
            host=target.host,
            port=target.port,
            database=target.database,
            query=target.options,
        )
        return str(url)

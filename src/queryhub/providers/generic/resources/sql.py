"""SQL database query provider.

This provider executes SQL queries against any SQL-compatible database
using SQLAlchemy's async support.
"""

from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from ....config.models import SQLProviderConfig
from ....core.credentials import CredentialRegistry
from ....core.errors import ProviderExecutionError
from ...base_credentials import BaseCredential
from ...base_query_provider import BaseQueryProvider, QueryResult


class SQLQueryProvider(BaseQueryProvider):
    """Execute SQL queries using SQLAlchemy.

    This provider is cloud-agnostic and works with any SQL database
    supported by SQLAlchemy (PostgreSQL, MySQL, SQL Server, etc.).
    """

    def __init__(
        self,
        config: SQLProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        super().__init__(config, credential_registry)
        self._credential: Optional[BaseCredential] = None
        self._engine: Optional[AsyncEngine] = None
        self._engine_lock = asyncio.Lock()
        self._sessionmaker: Optional[async_sessionmaker] = None

    @property
    def config(self) -> SQLProviderConfig:
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Execute a SQL query.

        Args:
            query: Query specification with keys:
                  - text: SQL query string (required)
                  - parameters: Optional query parameters
                  - timeout_seconds: Optional query timeout
        """
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
        """Close SQL engine and credential resources."""
        if self._engine is not None:
            await self._engine.dispose()
        if self._credential is not None:
            await self._credential.close()

    async def _get_engine(self) -> AsyncEngine:
        """Get or create SQL engine (lazy initialization with thread safety)."""
        if self._engine is not None:
            return self._engine
        async with self._engine_lock:
            if self._engine is None:
                self._engine = await self._create_engine()
        return self._engine

    async def _create_engine(self) -> AsyncEngine:
        """Create SQL engine using credential from registry."""
        target = self.config.target

        # Separate SQLAlchemy engine options from connection options
        engine_options = {"echo", "pool_size", "pool_recycle", "max_overflow", "pool_timeout"}
        connect_args: dict[str, Any] = {
            k: v for k, v in target.options.items() if k not in engine_options
        }
        engine_kwargs: dict[str, Any] = {
            k: v for k, v in target.options.items() if k in engine_options
        }

        # Get credential from registry
        if self.credential_registry and self.config.credentials:
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
        else:
            cred_data = None

        # Build connection URL
        url = self._build_url(target, cred_data)

        # Handle token-based auth (e.g., Azure SQL with AAD tokens)
        if isinstance(cred_data, dict) and "token" in cred_data:
            connect_args.setdefault("access_token", cred_data["token"])

        engine = create_async_engine(
            url, connect_args=connect_args, pool_pre_ping=True, **engine_kwargs
        )
        self._sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
        return engine

    def _build_url(self, target, cred_data) -> str:
        """Build SQLAlchemy connection URL."""
        # If connection string provided, use it directly
        if isinstance(cred_data, str):
            return cred_data

        # If DSN provided in target, use it
        if target.dsn:
            return str(target.dsn)

        # Otherwise, build URL from components
        driver = target.driver or "postgresql+asyncpg"
        username = None
        password = None

        if isinstance(cred_data, dict):
            username = cred_data.get("username")
            password = cred_data.get("password")

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

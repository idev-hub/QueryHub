"""Generic credential implementations.

This module contains credential strategies that work across multiple
cloud providers and resource types (SQL databases, REST APIs, etc.).
"""

from __future__ import annotations

from typing import Any

from ...config.credential_models import GenericCredentialConfig
from ..base_credentials import BaseCredential


class UsernamePasswordCredential(BaseCredential[GenericCredentialConfig, dict[str, str]]):
    """Username/password authentication.

    Works with: SQL databases, REST APIs (Basic Auth), any service that
    accepts username/password credentials.
    """

    def __init__(self, config: GenericCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> dict[str, str]:
        """Get username/password as a dict.

        Returns:
            Dict with 'username' and 'password' keys
        """
        assert self.config is not None, "Config is required"
        assert self.config.username is not None, "Username is required"
        assert self.config.password is not None, "Password is required"
        return {
            "username": self.config.username,
            "password": self.config.password.get_secret_value(),
        }


class TokenCredential(BaseCredential[GenericCredentialConfig, dict[str, str]]):
    """Token-based authentication (API keys, bearer tokens, etc.).

    Works with: REST APIs, any service that accepts token authentication.
    """

    def __init__(self, config: GenericCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> dict[str, str]:
        """Get token with header information.

        Returns:
            Dict with 'token', 'header_name', and 'template' keys
        """
        assert self.config is not None, "Config is required"
        assert self.config.token is not None, "Token is required"
        return {
            "token": self.config.token.get_secret_value(),
            "header_name": getattr(self.config, "header_name", "Authorization"),
            "template": getattr(self.config, "template", "Bearer {token}"),
        }


class ConnectionStringCredential(BaseCredential[GenericCredentialConfig, str]):
    """Connection string authentication.

    Works with: SQL databases, message queues, any service that uses
    connection strings.
    """

    def __init__(self, config: GenericCredentialConfig) -> None:
        super().__init__(config)

    async def get_connection(self, **context: Any) -> str:
        """Get connection string.

        Returns:
            Connection string
        """
        assert self.config is not None, "Config is required"
        assert self.config.connection_string is not None, "Connection string is required"
        return self.config.connection_string.get_secret_value()


class NoCredential(BaseCredential[None, None]):
    """No authentication required.

    Works with: Public APIs, local file systems, any resource that doesn't
    require authentication.
    """

    async def get_connection(self, **context: Any) -> None:
        """No authentication - returns None."""
        return None

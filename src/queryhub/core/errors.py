"""Centralized error hierarchy for QueryHub."""

from __future__ import annotations


class QueryHubError(Exception):
    """Base exception for all QueryHub errors."""


class ConfigurationError(QueryHubError):
    """Raised when configuration is invalid or incomplete."""


class ProviderError(QueryHubError):
    """Base exception for provider-related errors."""


class ProviderExecutionError(ProviderError):
    """Raised when a provider fails to execute a query."""


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not registered."""


class ProviderInitializationError(ProviderError):
    """Raised when a provider fails to initialize."""


class RenderingError(QueryHubError):
    """Raised when rendering fails."""


class TemplateError(QueryHubError):
    """Raised when template processing fails."""


class EmailError(QueryHubError):
    """Raised when email operations fail."""


class ExecutionTimeoutError(QueryHubError):
    """Raised when execution exceeds timeout."""


class ResourceError(QueryHubError):
    """Raised when resource operations fail."""

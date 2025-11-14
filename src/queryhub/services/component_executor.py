"""Component execution service following Single Responsibility Principle."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from ..config.models import QueryComponentConfig
from ..core.contracts import ProviderFactoryProtocol, RendererResolverProtocol
from ..core.errors import ProviderExecutionError, ExecutionTimeoutError, RenderingError
from ..core.retry import ExponentialBackoffRetry, RetryPolicy
from ..providers import QueryProvider, QueryResult

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ComponentExecutionResult:
    """Result of executing a single report component."""

    component: QueryComponentConfig
    result: QueryResult | None
    rendered_html: str | None
    error: Exception | None
    attempts: int
    duration_seconds: float

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.error is None

    @property
    def has_data(self) -> bool:
        """Check if result has data."""
        return self.result is not None and self.result.data is not None


class ProviderResolver:
    """Manages provider lifecycle with lazy initialization and caching."""

    def __init__(self, provider_factory: ProviderFactoryProtocol) -> None:
        self._factory = provider_factory
        self._providers: dict[str, QueryProvider] = {}
        self._lock = asyncio.Lock()

    async def get_provider(self, provider_id: str) -> QueryProvider:
        """Get or create a provider instance (thread-safe lazy loading)."""
        if provider_id in self._providers:
            return self._providers[provider_id]

        async with self._lock:
            if provider_id in self._providers:
                return self._providers[provider_id]

            provider = self._factory.create(provider_id)
            self._providers[provider_id] = provider
            return provider

    async def close_all(self) -> None:
        """Close all managed providers."""
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning("Failed to close provider %s: %s", provider, exc, exc_info=True)


class ComponentExecutor:
    """Executes individual report components with proper error handling."""

    def __init__(
        self,
        provider_resolver: ProviderResolver,
        renderer_resolver: RendererResolverProtocol,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._renderer_resolver = renderer_resolver

    async def execute(
        self,
        component: QueryComponentConfig,
    ) -> ComponentExecutionResult:
        """Execute a single component with retry, timeout, and rendering."""
        start_time = time.perf_counter()

        try:
            provider = await self._provider_resolver.get_provider(component.provider_id)
            result, attempts = await self._execute_query_with_retry(component, provider)
            rendered_html = await self._render_result(component, result)
            error = None
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.exception("Component %s execution failed", component.id)
            result = None
            rendered_html = None
            error = exc
            attempts = 0

        duration = time.perf_counter() - start_time

        return ComponentExecutionResult(
            component=component,
            result=result,
            rendered_html=rendered_html,
            error=error,
            attempts=attempts,
            duration_seconds=duration,
        )

    async def _execute_query_with_retry(
        self,
        component: QueryComponentConfig,
        provider: QueryProvider,
    ) -> tuple[QueryResult, int]:
        """Execute query with retry policy."""
        retry_policy = self._build_retry_policy(component, provider)
        retry_strategy = ExponentialBackoffRetry[QueryResult](retry_policy)

        attempts = 0

        async def operation() -> QueryResult:
            nonlocal attempts
            attempts += 1
            timeout = component.timeout_seconds or provider.config.default_timeout_seconds

            try:
                if timeout:
                    return await asyncio.wait_for(
                        provider.execute(component.query),
                        timeout=timeout,
                    )
                return await provider.execute(component.query)
            except asyncio.TimeoutError as exc:
                raise ExecutionTimeoutError(
                    f"Component '{component.id}' timed out after {timeout}s"
                ) from exc

        def should_retry(exc: Exception) -> bool:
            # Don't retry on timeout errors
            return not isinstance(exc, ExecutionTimeoutError)

        result = await retry_strategy.execute(operation, should_retry=should_retry)
        return result, attempts

    async def _render_result(
        self,
        component: QueryComponentConfig,
        result: QueryResult,
    ) -> str:
        """Render component result to HTML."""
        try:
            renderer = self._renderer_resolver.resolve(component.render)
            return renderer.render(component, result)
        except Exception as exc:
            raise RenderingError(
                f"Failed to render component '{component.id}': {exc}"
            ) from exc

    def _build_retry_policy(
        self,
        component: QueryComponentConfig,
        provider: QueryProvider,
    ) -> RetryPolicy:
        """Build retry policy from component and provider config."""
        max_attempts = (
            component.retries
            if component.retries is not None
            else provider.config.retry_attempts
        )
        backoff_seconds = provider.config.retry_backoff_seconds

        return RetryPolicy(
            max_attempts=max(1, max_attempts),
            backoff_seconds=backoff_seconds,
            backoff_multiplier=1.0,
            max_backoff_seconds=30.0,
        )

"""Retry logic abstraction following the Decorator pattern."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    backoff_seconds: float = 1.5
    backoff_multiplier: float = 1.0
    max_backoff_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds must be non-negative")
        if self.backoff_multiplier < 0:
            raise ValueError("backoff_multiplier must be non-negative")


class RetryStrategy(ABC, Generic[T]):
    """Abstract strategy for retry logic."""

    @abstractmethod
    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        should_retry: Callable[[Exception], bool] | None = None,
    ) -> T:
        """Execute operation with retry logic."""


class ExponentialBackoffRetry(RetryStrategy[T]):
    """Retry with exponential backoff."""

    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        should_retry: Callable[[Exception], bool] | None = None,
    ) -> T:
        """Execute operation with exponential backoff retry."""
        last_exception: Exception | None = None

        for attempt in range(self._policy.max_attempts):
            try:
                return await operation()
            except Exception as exc:  # pylint: disable=broad-except
                last_exception = exc

                if should_retry and not should_retry(exc):
                    raise

                if attempt < self._policy.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    _LOGGER.debug(
                        "Attempt %d/%d failed: %s. Retrying in %.2fs",
                        attempt + 1,
                        self._policy.max_attempts,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    _LOGGER.error(
                        "All %d attempts failed. Last error: %s",
                        self._policy.max_attempts,
                        exc,
                    )

        raise last_exception or RuntimeError("Retry failed with no exception")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        if self._policy.backoff_multiplier == 0:
            return self._policy.backoff_seconds

        delay = self._policy.backoff_seconds * (
            self._policy.backoff_multiplier ** attempt
        )
        return min(delay, self._policy.max_backoff_seconds)


class NoRetry(RetryStrategy[T]):
    """No retry strategy (single attempt only)."""

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        should_retry: Callable[[Exception], bool] | None = None,
    ) -> T:
        """Execute operation without retry."""
        return await operation()

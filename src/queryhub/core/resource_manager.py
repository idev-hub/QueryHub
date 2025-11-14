"""Resource lifecycle management following SOLID principles."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import AsyncContextManager, Generic, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncResource(ABC, Generic[T]):
    """Abstract base for resources requiring lifecycle management."""

    @abstractmethod
    async def acquire(self) -> T:
        """Acquire and return the resource."""

    @abstractmethod
    async def release(self, resource: T) -> None:
        """Release the resource and cleanup."""


class ResourcePool(Generic[T]):
    """Thread-safe lazy resource pool with proper lifecycle management."""

    def __init__(self, factory: AsyncResource[T]) -> None:
        self._factory = factory
        self._resource: T | None = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def get(self) -> T:
        """Get or create the resource (lazy initialization)."""
        if self._initialized and self._resource is not None:
            return self._resource

        async with self._lock:
            if self._initialized and self._resource is not None:
                return self._resource

            self._resource = await self._factory.acquire()
            self._initialized = True
            return self._resource

    async def close(self) -> None:
        """Release the resource if initialized."""
        if not self._initialized or self._resource is None:
            return

        async with self._lock:
            if self._resource is not None:
                try:
                    await self._factory.release(self._resource)
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.warning("Error releasing resource: %s", exc, exc_info=True)
                finally:
                    self._resource = None
                    self._initialized = False


class ResourceManager:
    """Manages multiple resources with proper cleanup coordination."""

    def __init__(self) -> None:
        self._resources: list[ResourcePool] = []
        self._exit_stack = AsyncExitStack()

    def register_pool(self, pool: ResourcePool) -> None:
        """Register a resource pool for managed cleanup."""
        self._resources.append(pool)

    def register_context(self, context: AsyncContextManager) -> None:
        """Register an async context manager for cleanup."""
        self._exit_stack.enter_async_context(context)

    async def close_all(self) -> None:
        """Close all registered resources in reverse order."""
        # Close resource pools
        for pool in reversed(self._resources):
            try:
                await pool.close()
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.error("Failed to close resource pool: %s", exc, exc_info=True)

        # Close context managers
        try:
            await self._exit_stack.aclose()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Failed to close context managers: %s", exc, exc_info=True)

    async def __aenter__(self) -> ResourceManager:
        """Support async context manager protocol."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure cleanup on exit."""
        await self.close_all()

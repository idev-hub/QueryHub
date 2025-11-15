"""Tests for retry logic."""

from __future__ import annotations

import pytest

from queryhub.core.retry import (
    ExponentialBackoffRetry,
    NoRetry,
    RetryPolicy,
)


def test_retry_policy_defaults() -> None:
    """Test RetryPolicy with default values."""
    policy = RetryPolicy()
    assert policy.max_attempts == 3
    assert policy.backoff_seconds == 1.5
    assert policy.backoff_multiplier == 1.0
    assert policy.max_backoff_seconds == 60.0


def test_retry_policy_custom_values() -> None:
    """Test RetryPolicy with custom values."""
    policy = RetryPolicy(
        max_attempts=5,
        backoff_seconds=2.0,
        backoff_multiplier=2.0,
        max_backoff_seconds=120.0,
    )
    assert policy.max_attempts == 5
    assert policy.backoff_seconds == 2.0
    assert policy.backoff_multiplier == 2.0
    assert policy.max_backoff_seconds == 120.0


def test_retry_policy_validation_max_attempts() -> None:
    """Test RetryPolicy validation for max_attempts."""
    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        RetryPolicy(max_attempts=0)


def test_retry_policy_validation_backoff_seconds() -> None:
    """Test RetryPolicy validation for backoff_seconds."""
    with pytest.raises(ValueError, match="backoff_seconds must be non-negative"):
        RetryPolicy(backoff_seconds=-1.0)


def test_retry_policy_validation_backoff_multiplier() -> None:
    """Test RetryPolicy validation for backoff_multiplier."""
    with pytest.raises(ValueError, match="backoff_multiplier must be non-negative"):
        RetryPolicy(backoff_multiplier=-1.0)


@pytest.mark.asyncio
async def test_no_retry_success() -> None:
    """Test NoRetry strategy with successful operation."""
    strategy = NoRetry[int]()
    call_count = 0

    async def operation() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    result = await strategy.execute(operation)
    assert result == 42
    assert call_count == 1


@pytest.mark.asyncio
async def test_no_retry_failure() -> None:
    """Test NoRetry strategy with failing operation."""
    strategy = NoRetry[int]()

    async def operation() -> int:
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await strategy.execute(operation)


@pytest.mark.asyncio
async def test_exponential_backoff_success_first_attempt() -> None:
    """Test ExponentialBackoffRetry with immediate success."""
    policy = RetryPolicy(max_attempts=3, backoff_seconds=0.1)
    strategy = ExponentialBackoffRetry[int](policy)
    call_count = 0

    async def operation() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    result = await strategy.execute(operation)
    assert result == 42
    assert call_count == 1


@pytest.mark.asyncio
async def test_exponential_backoff_success_second_attempt() -> None:
    """Test ExponentialBackoffRetry with success on second attempt."""
    policy = RetryPolicy(max_attempts=3, backoff_seconds=0.01)
    strategy = ExponentialBackoffRetry[int](policy)
    call_count = 0

    async def operation() -> int:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First attempt fails")
        return 42

    result = await strategy.execute(operation)
    assert result == 42
    assert call_count == 2


@pytest.mark.asyncio
async def test_exponential_backoff_all_attempts_fail() -> None:
    """Test ExponentialBackoffRetry when all attempts fail."""
    policy = RetryPolicy(max_attempts=3, backoff_seconds=0.01)
    strategy = ExponentialBackoffRetry[int](policy)
    call_count = 0

    async def operation() -> int:
        nonlocal call_count
        call_count += 1
        raise ValueError(f"Attempt {call_count} failed")

    with pytest.raises(ValueError, match="Attempt 3 failed"):
        await strategy.execute(operation)
    assert call_count == 3


@pytest.mark.asyncio
async def test_exponential_backoff_with_should_retry() -> None:
    """Test ExponentialBackoffRetry with should_retry predicate."""
    policy = RetryPolicy(max_attempts=3, backoff_seconds=0.01)
    strategy = ExponentialBackoffRetry[int](policy)

    async def operation() -> int:
        raise ValueError("Non-retryable error")

    def should_retry(exc: Exception) -> bool:
        return not isinstance(exc, ValueError)

    with pytest.raises(ValueError, match="Non-retryable error"):
        await strategy.execute(operation, should_retry)


@pytest.mark.asyncio
async def test_exponential_backoff_delay_calculation() -> None:
    """Test ExponentialBackoffRetry calculates delays correctly."""
    policy = RetryPolicy(
        max_attempts=4,
        backoff_seconds=1.0,
        backoff_multiplier=2.0,
        max_backoff_seconds=10.0,
    )
    strategy = ExponentialBackoffRetry[int](policy)

    # Test delay calculation
    assert strategy._calculate_delay(0) == 1.0  # 1.0 * (2.0 ^ 0)
    assert strategy._calculate_delay(1) == 2.0  # 1.0 * (2.0 ^ 1)
    assert strategy._calculate_delay(2) == 4.0  # 1.0 * (2.0 ^ 2)
    assert strategy._calculate_delay(3) == 8.0  # 1.0 * (2.0 ^ 3)


@pytest.mark.asyncio
async def test_exponential_backoff_max_delay() -> None:
    """Test ExponentialBackoffRetry respects max_backoff_seconds."""
    policy = RetryPolicy(
        max_attempts=4,
        backoff_seconds=1.0,
        backoff_multiplier=2.0,
        max_backoff_seconds=5.0,
    )
    strategy = ExponentialBackoffRetry[int](policy)

    # Should cap at max_backoff_seconds
    assert strategy._calculate_delay(3) == 5.0  # Would be 8.0, but capped at 5.0
    assert strategy._calculate_delay(10) == 5.0  # Always capped


@pytest.mark.asyncio
async def test_exponential_backoff_zero_multiplier() -> None:
    """Test ExponentialBackoffRetry with zero multiplier (constant backoff)."""
    policy = RetryPolicy(
        max_attempts=3,
        backoff_seconds=1.0,
        backoff_multiplier=0.0,
        max_backoff_seconds=10.0,
    )
    strategy = ExponentialBackoffRetry[int](policy)

    # All delays should be constant
    assert strategy._calculate_delay(0) == 1.0
    assert strategy._calculate_delay(1) == 1.0
    assert strategy._calculate_delay(2) == 1.0

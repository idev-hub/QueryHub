# Migration Guide

This guide helps you migrate code that uses the old QueryHub APIs to the refactored version.

## Overview

The refactoring maintains backward compatibility for all public APIs. Most code will continue to work without changes. However, some internal imports have changed.

## Error Handling

### Before
```python
from queryhub.providers import ProviderExecutionError

try:
    result = await provider.execute(query)
except ProviderExecutionError as e:
    print(f"Provider failed: {e}")
```

### After
```python
from queryhub.core.errors import ProviderExecutionError

try:
    result = await provider.execute(query)
except ProviderExecutionError as e:
    print(f"Provider failed: {e}")
```

### Recommended (New)
```python
from queryhub.core.errors import ProviderError, QueryHubError

try:
    result = await provider.execute(query)
except ProviderError as e:
    # Catches all provider-related errors
    print(f"Provider error: {e}")
except QueryHubError as e:
    # Catches any QueryHub error
    print(f"QueryHub error: {e}")
```

## Component Execution

### Before
```python
from queryhub.services import ComponentExecutionResult

# ComponentExecutionResult was embedded in executor.py
```

### After
```python
from queryhub.services import ComponentExecutionResult

# Now properly exposed from services module
result = ComponentExecutionResult(...)
print(result.is_success)  # New convenience method
```

## Provider Registry

### Before
```python
# Direct instantiation (internal API)
from queryhub.core.providers import DefaultProviderFactory

factory = DefaultProviderFactory(configs, registry)
```

### After
```python
# Same API, but better error handling
from queryhub.core.providers import DefaultProviderFactory
from queryhub.core.errors import ProviderNotFoundError

factory = DefaultProviderFactory(configs, registry)
try:
    provider = factory.create("unknown")
except ProviderNotFoundError as e:
    print(f"Provider not found: {e}")
```

## Configuration Loading

### Before
```python
from queryhub.config import ConfigLoader

loader = ConfigLoader("/path/to/config")
settings = loader.load_sync()
```

### After
```python
from queryhub.config import ConfigLoader
from queryhub.core.errors import ConfigurationError

loader = ConfigLoader("/path/to/config")
try:
    settings = loader.load_sync()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Email Sending

### Before
```python
from queryhub.email.client import EmailClient

client = EmailClient(smtp_config)
await client.send_report(result)
```

### After
```python
from queryhub.email.client import EmailClient
from queryhub.core.errors import EmailError

client = EmailClient(smtp_config)
try:
    await client.send_report(result)
except EmailError as e:
    print(f"Email error: {e}")
```

## Rendering

### Before
```python
from queryhub.rendering.renderers import TableRenderer

renderer = TableRenderer()
html = renderer.render(component, result)
```

### After
```python
from queryhub.rendering.renderers import TableRenderer
from queryhub.core.errors import RenderingError

renderer = TableRenderer()
try:
    html = renderer.render(component, result)
except RenderingError as e:
    print(f"Rendering error: {e}")
```

## Testing with New Architecture

### Mocking Providers

```python
from unittest.mock import AsyncMock
from queryhub.providers.base import QueryProvider, QueryResult

# Create a mock provider
mock_provider = AsyncMock(spec=QueryProvider)
mock_provider.execute.return_value = QueryResult(
    data=[{"id": 1, "name": "test"}],
    metadata={}
)
```

### Dependency Injection

```python
from queryhub.services import QueryHubApplicationBuilder

# Inject custom dependencies for testing
builder = QueryHubApplicationBuilder(
    config_dir=test_config_dir,
    templates_dir=test_templates_dir,
    provider_factory=mock_factory,  # Your test factory
    renderer_resolver=mock_registry,  # Your test registry
)
executor = await builder.create_executor()
```

## New Features You Can Use

### 1. Centralized Error Handling

```python
from queryhub.core.errors import QueryHubError

try:
    result = await executor.execute_report("my_report")
except QueryHubError as e:
    # All QueryHub exceptions inherit from this
    logger.error(f"Report failed: {e}")
    # Handle gracefully
```

### 2. Immutable Result Objects

```python
result = await executor.execute_report("my_report")

# Results are now immutable (frozen dataclasses)
print(result.success_count)  # New property
print(result.failure_count)  # New property
print(result.has_failures)   # Existing property
```

### 3. Resource Management

```python
from queryhub.core.resource_manager import ResourceManager

async with ResourceManager() as manager:
    # Resources are automatically cleaned up
    pool = ResourcePool(my_resource_factory)
    manager.register_pool(pool)
    resource = await pool.get()
    # Use resource
# Automatic cleanup happens here
```

### 4. Retry Strategies

```python
from queryhub.core.retry import ExponentialBackoffRetry, RetryPolicy

policy = RetryPolicy(
    max_attempts=5,
    backoff_seconds=2.0,
    backoff_multiplier=2.0,
    max_backoff_seconds=60.0,
)
retry = ExponentialBackoffRetry(policy)

async def risky_operation():
    # Your operation here
    pass

result = await retry.execute(risky_operation)
```

## Breaking Changes

**None.** All public APIs remain backward compatible.

## Deprecations

**None.** No APIs are deprecated in this release.

## Internal API Changes

If you were using internal APIs (not recommended), note these changes:

1. `ProviderExecutionError` moved from `providers.base` to `core.errors`
2. Component execution logic moved to `services.component_executor`
3. Config parsing split into multiple focused classes
4. Email client split into focused classes

## Recommendations

1. **Update error imports** to use `core.errors` module
2. **Use typed exceptions** for better error handling
3. **Leverage new convenience methods** on result objects
4. **Consider using ResourceManager** for custom resources
5. **Use dependency injection** via `QueryHubApplicationBuilder` for better testing

## Questions?

If you have questions about the migration, please:
1. Check the [Architecture Documentation](solid-architecture.md)
2. Review the [Refactoring Summary](refactoring-summary.md)
3. Look at the test files for examples
4. Open an issue on GitHub

## Summary

✅ **No breaking changes** - Your code should continue to work
✅ **Better error handling** - Use typed exceptions from `core.errors`
✅ **More features** - New convenience methods and utilities
✅ **Better architecture** - Cleaner, more maintainable code
✅ **Same performance** - No performance regressions

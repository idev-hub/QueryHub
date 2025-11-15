"""Tests for credential registry."""

from __future__ import annotations

import pytest

from queryhub.config.models import (
    AWSAccessKeyCredential,
    ConnectionStringCredential,
    CredentialType,
    DefaultCredentialConfig,
    EmptyCredential,
)
from queryhub.core.credentials import CredentialRegistry
from queryhub.core.errors import ProviderInitializationError


def test_credential_registry_init_empty() -> None:
    """Test creating empty credential registry."""
    registry = CredentialRegistry()
    assert len(registry) == 0
    assert registry.list_credential_ids() == []


def test_credential_registry_register_and_get() -> None:
    """Test registering and retrieving a credential."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    registry.register("test_cred", "generic", "none", config)

    assert len(registry) == 1
    assert "test_cred" in registry
    assert registry.list_credential_ids() == ["test_cred"]


def test_credential_registry_get_credential_caching() -> None:
    """Test that credentials are cached."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    registry.register("cached_cred", "generic", "none", config)

    # Get credential twice
    cred1 = registry.get_credential("cached_cred")
    cred2 = registry.get_credential("cached_cred")

    # Should be the same instance (cached)
    assert cred1 is cred2


def test_credential_registry_get_not_found() -> None:
    """Test getting non-existent credential raises error."""
    registry = CredentialRegistry()

    with pytest.raises(
        ProviderInitializationError,
        match="Credential 'missing' not found in registry",
    ):
        registry.get_credential("missing")


def test_credential_registry_get_invalid_type() -> None:
    """Test getting credential with invalid type raises error."""
    registry = CredentialRegistry()

    with pytest.raises(
        ProviderInitializationError,
        match="Credential reference must be a string ID",
    ):
        registry.get_credential(123)  # type: ignore[arg-type]


def test_credential_registry_register_overwrite() -> None:
    """Test that re-registering a credential clears cache."""
    registry = CredentialRegistry()
    config1 = EmptyCredential(type=CredentialType.NONE)
    config2 = EmptyCredential(type=CredentialType.NONE)

    registry.register("cred", "generic", "none", config1)
    cred1 = registry.get_credential("cred")

    # Re-register with new config
    registry.register("cred", "generic", "none", config2)
    cred2 = registry.get_credential("cred")

    # Should be different instances since cache was cleared
    assert cred1 is not cred2


def test_credential_registry_multiple_credentials() -> None:
    """Test registering multiple credentials."""
    registry = CredentialRegistry()

    config1 = EmptyCredential(type=CredentialType.NONE)
    config2 = DefaultCredentialConfig(type=CredentialType.DEFAULT_CREDENTIALS)

    registry.register("cred1", "generic", "none", config1)
    registry.register("cred2", "azure", "default_credentials", config2)

    assert len(registry) == 2
    assert "cred1" in registry
    assert "cred2" in registry
    assert set(registry.list_credential_ids()) == {"cred1", "cred2"}


def test_credential_registry_contains() -> None:
    """Test __contains__ method."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    assert "test" not in registry
    registry.register("test", "generic", "none", config)
    assert "test" in registry


@pytest.mark.asyncio
async def test_credential_registry_close_all() -> None:
    """Test closing all credentials."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    registry.register("cred1", "generic", "none", config)
    registry.register("cred2", "generic", "none", config)

    # Get credentials to populate cache
    registry.get_credential("cred1")
    registry.get_credential("cred2")

    # Close all should clear cache
    await registry.close_all()

    # Cache should be cleared, but registry should still have definitions
    assert len(registry) == 2
    # Getting credential again should create new instance
    cred = registry.get_credential("cred1")
    assert cred is not None


def test_credential_registry_init_with_credentials() -> None:
    """Test initializing registry with existing credentials."""
    config = EmptyCredential(type=CredentialType.NONE)
    initial_creds = {
        "cred1": ("generic", "none", config),
        "cred2": ("generic", "none", config),
    }

    registry = CredentialRegistry(credentials=initial_creds)

    assert len(registry) == 2
    assert "cred1" in registry
    assert "cred2" in registry


def test_credential_registry_list_credential_ids() -> None:
    """Test listing credential IDs."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    registry.register("alpha", "generic", "none", config)
    registry.register("beta", "generic", "none", config)
    registry.register("gamma", "generic", "none", config)

    ids = registry.list_credential_ids()
    assert set(ids) == {"alpha", "beta", "gamma"}


def test_credential_registry_get_with_cloud_provider_override() -> None:
    """Test getting credential with cloud provider override."""
    registry = CredentialRegistry()
    config = EmptyCredential(type=CredentialType.NONE)

    registry.register("test_cred", "generic", "none", config)

    # Get with override (should still work with generic credentials)
    cred = registry.get_credential("test_cred", cloud_provider="generic")
    assert cred is not None

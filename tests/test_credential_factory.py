"""Tests for credential factory."""

from __future__ import annotations

import pytest

from queryhub.config.models import (
    AWSAccessKeyCredential,
    AWSIAMRoleCredential,
    ConnectionStringCredential,
    CredentialType,
    DefaultCredentialConfig,
    EmptyCredential,
    TokenCredential,
)
from queryhub.core.errors import ProviderInitializationError
from queryhub.providers.credential_factory import create_credential
from pydantic import SecretStr


def test_create_credential_generic_none() -> None:
    """Test creating generic 'none' credential."""
    config = EmptyCredential(type=CredentialType.NONE)
    credential = create_credential(config, "generic", "none")

    assert credential is not None
    from queryhub.providers.generic.credentials import NoCredential

    assert isinstance(credential, NoCredential)


def test_create_credential_generic_token() -> None:
    """Test creating generic token credential."""
    config = TokenCredential(
        type=CredentialType.TOKEN,
        token=SecretStr("test_token"),
    )
    credential = create_credential(config, "generic", "token")

    assert credential is not None
    from queryhub.providers.generic.credentials import TokenCredential as GenericTokenCredential

    assert isinstance(credential, GenericTokenCredential)


def test_create_credential_generic_connection_string() -> None:
    """Test creating generic connection string credential."""
    config = ConnectionStringCredential(
        type=CredentialType.CONNECTION_STRING,
        connection_string=SecretStr("host=localhost;database=test"),
    )
    credential = create_credential(config, "generic", "connection_string")

    assert credential is not None
    from queryhub.providers.generic.credentials import ConnectionStringCredential as GenericConnStr

    assert isinstance(credential, GenericConnStr)


def test_create_credential_azure_default() -> None:
    """Test creating Azure default credential."""
    config = DefaultCredentialConfig(type=CredentialType.DEFAULT_CREDENTIALS)
    credential = create_credential(config, "azure", "default_credentials")

    assert credential is not None
    from queryhub.providers.azure.credentials import AzureDefaultCredential

    assert isinstance(credential, AzureDefaultCredential)


def test_create_credential_aws_default() -> None:
    """Test creating AWS default credential."""
    config = DefaultCredentialConfig(type=CredentialType.DEFAULT_CREDENTIALS)
    credential = create_credential(config, "aws", "default_credentials")

    assert credential is not None
    from queryhub.providers.aws.credentials import AWSDefaultCredential

    assert isinstance(credential, AWSDefaultCredential)


def test_create_credential_aws_access_key() -> None:
    """Test creating AWS access key credential."""
    config = AWSAccessKeyCredential(
        type=CredentialType.ACCESS_KEY,
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        secret_access_key=SecretStr("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
    )
    credential = create_credential(config, "aws", "access_key")

    assert credential is not None
    from queryhub.providers.aws.credentials import AWSAccessKeyCredential as AWSAccessKey

    assert isinstance(credential, AWSAccessKey)


def test_create_credential_aws_iam_role() -> None:
    """Test creating AWS IAM role credential."""
    config = AWSIAMRoleCredential(
        type=CredentialType.IAM_ROLE,
        role_arn="arn:aws:iam::123456789012:role/test-role",
    )
    credential = create_credential(config, "aws", "iam_role")

    assert credential is not None
    from queryhub.providers.aws.credentials import AWSIAMRoleCredential as AWSIAMRole

    assert isinstance(credential, AWSIAMRole)


def test_create_credential_gcp_default() -> None:
    """Test creating GCP default credential."""
    config = DefaultCredentialConfig(type=CredentialType.DEFAULT_CREDENTIALS)
    credential = create_credential(config, "gcp", "default_credentials")

    assert credential is not None
    from queryhub.providers.gcp.credentials import GCPDefaultCredential

    assert isinstance(credential, GCPDefaultCredential)


def test_create_credential_unsupported_cloud_provider() -> None:
    """Test that unsupported cloud provider raises error."""
    config = EmptyCredential(type=CredentialType.NONE)

    with pytest.raises(
        ProviderInitializationError,
        match="Unsupported cloud provider: unknown",
    ):
        create_credential(config, "unknown", "none")


def test_create_credential_unsupported_azure_type() -> None:
    """Test that unsupported Azure credential type raises error."""
    config = EmptyCredential(type=CredentialType.NONE)

    with pytest.raises(
        ProviderInitializationError,
        match="Unsupported Azure credential type: invalid_type",
    ):
        create_credential(config, "azure", "invalid_type")


def test_create_credential_unsupported_aws_type() -> None:
    """Test that unsupported AWS credential type raises error."""
    config = EmptyCredential(type=CredentialType.NONE)

    with pytest.raises(
        ProviderInitializationError,
        match="Unsupported AWS credential type: invalid_type",
    ):
        create_credential(config, "aws", "invalid_type")


def test_create_credential_unsupported_gcp_type() -> None:
    """Test that unsupported GCP credential type raises error."""
    config = EmptyCredential(type=CredentialType.NONE)

    with pytest.raises(
        ProviderInitializationError,
        match="Unsupported GCP credential type: invalid_type",
    ):
        create_credential(config, "gcp", "invalid_type")


def test_create_credential_unsupported_generic_type() -> None:
    """Test that unsupported generic credential type raises error."""
    config = EmptyCredential(type=CredentialType.NONE)

    with pytest.raises(
        ProviderInitializationError,
        match="Unsupported generic credential type: invalid_type",
    ):
        create_credential(config, "generic", "invalid_type")


def test_create_credential_postgresql_routes_to_generic() -> None:
    """Test that postgresql cloud provider routes to generic credentials."""
    config = EmptyCredential(type=CredentialType.NONE)
    credential = create_credential(config, "postgresql", "none")

    assert credential is not None
    from queryhub.providers.generic.credentials import NoCredential

    assert isinstance(credential, NoCredential)

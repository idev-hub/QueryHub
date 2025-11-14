"""Credential factory for creating credential instances.

This factory routes to the appropriate credential class based on
cloud provider and credential type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.errors import ProviderInitializationError
from .base_credentials import BaseCredential

if TYPE_CHECKING:
    from ..config.models import CredentialConfig


def create_credential(
    config: CredentialConfig,
    cloud_provider: str,
    credential_type: str,
) -> BaseCredential:
    """Factory function to create the appropriate credential instance.

    This is the single entry point for credential creation. It routes to
    the appropriate credential class based on cloud provider and type.

    Args:
        config: Credential configuration from YAML
        cloud_provider: Cloud provider (azure, aws, gcp, generic)
        credential_type: Credential type (default_credentials, access_key, etc.)

    Returns:
        Appropriate BaseCredential instance

    Raises:
        ProviderInitializationError: If credential type is unsupported
    """
    if cloud_provider == "azure":
        return _create_azure_credential(config, credential_type)
    elif cloud_provider == "aws":
        return _create_aws_credential(config, credential_type)
    elif cloud_provider == "gcp":
        return _create_gcp_credential(config, credential_type)
    elif cloud_provider == "generic" or cloud_provider == "postgresql":
        return _create_generic_credential(config, credential_type)
    else:
        raise ProviderInitializationError(
            f"Unsupported cloud provider: {cloud_provider}. Supported: azure, aws, gcp, generic"
        )


def _create_azure_credential(config: CredentialConfig, credential_type: str) -> BaseCredential:
    """Create Azure credential."""
    from .azure.credentials import (
        AzureDefaultCredential,
        AzureManagedIdentityCredential,
        AzureServicePrincipalCredential,
        AzureTokenCredential,
    )

    credential_map = {
        "default_credentials": AzureDefaultCredential,
        "managed_identity": AzureManagedIdentityCredential,
        "service_principal": AzureServicePrincipalCredential,
        "token": AzureTokenCredential,
    }

    credential_class = credential_map.get(credential_type)
    if not credential_class:
        raise ProviderInitializationError(
            f"Unsupported Azure credential type: {credential_type}. "
            f"Supported: {', '.join(credential_map.keys())}"
        )

    return credential_class(config)  # type: ignore[no-any-return]


def _create_aws_credential(config: CredentialConfig, credential_type: str) -> BaseCredential:
    """Create AWS credential."""
    from .aws.credentials import (
        AWSAccessKeyCredential,
        AWSDefaultCredential,
        AWSIAMRoleCredential,
    )

    credential_map = {
        "default_credentials": AWSDefaultCredential,
        "access_key": AWSAccessKeyCredential,
        "iam_role": AWSIAMRoleCredential,
    }

    credential_class = credential_map.get(credential_type)
    if not credential_class:
        raise ProviderInitializationError(
            f"Unsupported AWS credential type: {credential_type}. "
            f"Supported: {', '.join(credential_map.keys())}"
        )

    return credential_class(config)  # type: ignore[no-any-return]


def _create_gcp_credential(config: CredentialConfig, credential_type: str) -> BaseCredential:
    """Create GCP credential."""
    from .gcp.credentials import (
        GCPDefaultCredential,
        GCPServiceAccountJSONCredential,
    )

    credential_map = {
        "default_credentials": GCPDefaultCredential,
        "service_account": GCPServiceAccountJSONCredential,
        "service_account_json": GCPServiceAccountJSONCredential,
    }

    credential_class = credential_map.get(credential_type)
    if not credential_class:
        raise ProviderInitializationError(
            f"Unsupported GCP credential type: {credential_type}. "
            f"Supported: {', '.join(credential_map.keys())}"
        )

    return credential_class(config)  # type: ignore[no-any-return]


def _create_generic_credential(config: CredentialConfig, credential_type: str) -> BaseCredential:
    """Create generic credential."""
    from .generic.credentials import (
        ConnectionStringCredential,
        NoCredential,
        TokenCredential,
        UsernamePasswordCredential,
    )

    credential_map = {
        "username_password": UsernamePasswordCredential,
        "token": TokenCredential,
        "connection_string": ConnectionStringCredential,
        "none": NoCredential,
    }

    credential_class = credential_map.get(credential_type)
    if not credential_class:
        raise ProviderInitializationError(
            f"Unsupported generic credential type: {credential_type}. "
            f"Supported: {', '.join(credential_map.keys())}"
        )

    return credential_class(config)  # type: ignore[no-any-return]

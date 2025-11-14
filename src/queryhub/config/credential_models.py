"""New simplified credential models matching updated YAML structure.

The new YAML format has credentials organized by cloud provider:

credentials:
  - id: azure_default
    azure:
      type: default_credentials
  - id: postgres_creds
    postgresql:
      type: username_password
      username: user
      password: pass
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, SecretStr


# Azure Credential Configs
class AzureCredentialConfig(BaseModel):
    """Azure credential configuration."""

    type: str
    client_id: Optional[str] = None
    tenant_id: Optional[str] = None
    client_secret: Optional[SecretStr] = None
    token: Optional[SecretStr] = None
    model_config = ConfigDict(extra="allow")


# AWS Credential Configs
class AWSCredentialConfig(BaseModel):
    """AWS credential configuration."""

    type: str
    access_key_id: Optional[str] = None
    secret_access_key: Optional[SecretStr] = None
    session_token: Optional[SecretStr] = None
    role_arn: Optional[str] = None
    role_session_name: Optional[str] = None
    region: Optional[str] = None
    model_config = ConfigDict(extra="allow")


# GCP Credential Configs
class GCPCredentialConfig(BaseModel):
    """GCP credential configuration."""

    type: str
    service_account_json: Optional[SecretStr] = None
    service_account_json_path: Optional[str] = None
    project_id: Optional[str] = None
    model_config = ConfigDict(extra="allow")


# Generic/PostgreSQL Credential Configs
class GenericCredentialConfig(BaseModel):
    """Generic credential configuration (username/password, token, etc.)."""

    type: str
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    token: Optional[SecretStr] = None
    header_name: Optional[str] = "Authorization"
    template: Optional[str] = "Bearer {token}"
    connection_string: Optional[SecretStr] = None
    model_config = ConfigDict(extra="allow")


# Main Credential Config
class CredentialConfig(BaseModel):
    """Top-level credential configuration."""

    id: str
    azure: Optional[AzureCredentialConfig] = None
    aws: Optional[AWSCredentialConfig] = None
    gcp: Optional[GCPCredentialConfig] = None
    postgresql: Optional[GenericCredentialConfig] = None
    generic: Optional[GenericCredentialConfig] = None
    model_config = ConfigDict(extra="allow")

    def get_cloud_provider(self) -> str:
        """Determine the cloud provider from the config."""
        if self.azure:
            return "azure"
        elif self.aws:
            return "aws"
        elif self.gcp:
            return "gcp"
        elif self.postgresql:
            return "postgresql"
        elif self.generic:
            return "generic"
        else:
            return "generic"

    def get_credential_type(self) -> str:
        """Get the credential type."""
        if self.azure:
            return self.azure.type
        elif self.aws:
            return self.aws.type
        elif self.gcp:
            return self.gcp.type
        elif self.postgresql:
            return self.postgresql.type
        elif self.generic:
            return self.generic.type
        else:
            return "none"

    def get_credential_config(
        self,
    ) -> (
        AzureCredentialConfig | AWSCredentialConfig | GCPCredentialConfig | GenericCredentialConfig
    ):
        """Get the actual credential configuration."""
        if self.azure:
            return self.azure
        elif self.aws:
            return self.aws
        elif self.gcp:
            return self.gcp
        elif self.postgresql:
            return self.postgresql
        elif self.generic:
            return self.generic
        else:
            raise ValueError("No credential configuration found")

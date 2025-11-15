"""Typed configuration models for QueryHub."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    GENERIC = "generic"  # For SQL, REST, CSV that work with any cloud


class ProviderType(str, Enum):
    """Supported provider categories."""

    ADX = "adx"
    SQL = "sql"
    REST = "rest"
    CSV = "csv"
    S3 = "s3"
    ATHENA = "athena"
    BIGQUERY = "bigquery"


class CredentialType(str, Enum):
    """Credential types understood by core providers."""

    # Azure credential types
    DEFAULT_CREDENTIALS = "default_credentials"
    MANAGED_IDENTITY = "managed_identity"
    SERVICE_PRINCIPAL = "service_principal"

    # Generic credential types
    USERNAME_PASSWORD = "username_password"  # nosec B105 - enum value, not a password
    CONNECTION_STRING = "connection_string"
    TOKEN = "token"  # nosec B105 - enum value, not a token

    # AWS credential types
    ACCESS_KEY = "access_key"
    IAM_ROLE = "iam_role"

    # GCP credential types
    SERVICE_ACCOUNT = "service_account"
    SERVICE_ACCOUNT_JSON = "service_account_json"

    NONE = "none"


class BaseCredentialConfig(BaseModel):
    """Base credential definition with common options."""

    id: Optional[str] = None  # Optional ID for reusable credentials
    type: CredentialType
    cloud_provider: CloudProvider = CloudProvider.GENERIC
    model_config = ConfigDict(extra="forbid")


class DefaultCredentialConfig(BaseCredentialConfig):
    """Default credential chain (Azure DefaultAzureCredential, AWS default chain, GCP ADC)."""

    type: Literal[CredentialType.DEFAULT_CREDENTIALS]


class ManagedIdentityCredential(BaseCredentialConfig):
    type: Literal[CredentialType.MANAGED_IDENTITY]
    client_id: Optional[str] = None


class ServicePrincipalCredential(BaseCredentialConfig):
    type: Literal[CredentialType.SERVICE_PRINCIPAL]
    tenant_id: str
    client_id: str
    client_secret: SecretStr


class UsernamePasswordCredential(BaseCredentialConfig):
    type: Literal[CredentialType.USERNAME_PASSWORD]
    username: str
    password: SecretStr


class ConnectionStringCredential(BaseCredentialConfig):
    type: Literal[CredentialType.CONNECTION_STRING]
    connection_string: SecretStr


class TokenCredential(BaseCredentialConfig):
    type: Literal[CredentialType.TOKEN]
    token: SecretStr
    header_name: str = "Authorization"
    template: str = "Bearer {token}"


class AWSAccessKeyCredential(BaseCredentialConfig):
    """AWS access key and secret key credentials."""

    type: Literal[CredentialType.ACCESS_KEY]
    cloud_provider: Literal[CloudProvider.AWS] = CloudProvider.AWS
    access_key_id: str
    secret_access_key: SecretStr
    session_token: Optional[SecretStr] = None
    region: Optional[str] = None


class AWSIAMRoleCredential(BaseCredentialConfig):
    """AWS IAM role credentials."""

    type: Literal[CredentialType.IAM_ROLE]
    cloud_provider: Literal[CloudProvider.AWS] = CloudProvider.AWS
    role_arn: str
    role_session_name: Optional[str] = "queryhub-session"
    region: Optional[str] = None


class GCPServiceAccountCredential(BaseCredentialConfig):
    """GCP service account credentials."""

    type: Literal[CredentialType.SERVICE_ACCOUNT]
    cloud_provider: Literal[CloudProvider.GCP] = CloudProvider.GCP
    service_account_email: str
    private_key: SecretStr
    project_id: Optional[str] = None


class GCPServiceAccountJSONCredential(BaseCredentialConfig):
    """GCP service account JSON file credentials."""

    type: Literal[CredentialType.SERVICE_ACCOUNT_JSON]
    cloud_provider: Literal[CloudProvider.GCP] = CloudProvider.GCP
    service_account_json_path: Optional[str] = None
    service_account_json: Optional[SecretStr] = None  # Inline JSON
    project_id: Optional[str] = None


class EmptyCredential(BaseCredentialConfig):
    type: Literal[CredentialType.NONE] = CredentialType.NONE


CredentialConfig = (
    DefaultCredentialConfig
    | ManagedIdentityCredential
    | ServicePrincipalCredential
    | UsernamePasswordCredential
    | ConnectionStringCredential
    | TokenCredential
    | AWSAccessKeyCredential
    | AWSIAMRoleCredential
    | GCPServiceAccountCredential
    | GCPServiceAccountJSONCredential
    | EmptyCredential
)


class BaseProviderConfig(BaseModel):
    """Shared provider configuration attributes."""

    id: str
    type: ProviderType
    cloud_provider: CloudProvider = CloudProvider.GENERIC
    default_timeout_seconds: Optional[float] = Field(default=30.0, gt=0)
    retry_attempts: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=1.5, gt=0)
    # Supports both inline credentials and credential ID references
    credentials: Optional[Union[str, CredentialConfig]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid")


class ComponentRendererType(str, Enum):
    """Renderer types supported by the HTML report pipeline."""

    TABLE = "table"
    CHART = "chart"
    TEXT = "text"
    HTML = "html"


class ComponentRenderConfig(BaseModel):
    """Render instructions for a component."""

    type: ComponentRendererType
    template: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class QueryComponentConfig(BaseModel):
    """A single report component definition."""

    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    provider_id: str = Field(alias="provider")
    query: Dict[str, Any]
    render: ComponentRenderConfig
    timeout_seconds: Optional[float] = Field(default=None, gt=0)
    retries: Optional[int] = Field(default=None, ge=0)
    tags: Dict[str, str] = Field(default_factory=dict)
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ReportLayoutConfig(BaseModel):
    """Ordered layout definition for the report template."""

    sections: list[dict[str, Any]] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class ReportEmailConfig(BaseModel):
    """Email overrides defined at the report level."""

    to: list[str]
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject_template: Optional[str] = None
    from_address: Optional[str] = None
    reply_to: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class ReportScheduleConfig(BaseModel):
    """Scheduling metadata stored alongside report definitions."""

    cron: Optional[str] = None
    timezone: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class ReportConfig(BaseModel):
    """Configuration for a report execution."""

    id: str
    title: str
    description: Optional[str] = None
    template: str = "report.html.j2"
    components: list[QueryComponentConfig]
    layout: ReportLayoutConfig = Field(default_factory=ReportLayoutConfig)
    email: Optional[ReportEmailConfig] = None
    schedule: ReportScheduleConfig = Field(default_factory=ReportScheduleConfig)
    tags: Dict[str, str] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class SMTPAuthConfig(BaseModel):
    """SMTP authentication options."""

    username: Optional[str] = None
    password: Optional[SecretStr] = None
    dkim_selector: Optional[str] = None
    dkim_private_key_path: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class SMTPConfig(BaseModel):
    """Outgoing email configuration."""

    host: str
    port: int = 587
    use_tls: bool = True
    starttls: bool = True
    timeout_seconds: float = 30.0
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    default_from: Optional[str] = None
    default_to: list[str] = Field(default_factory=list)
    subject_template: Optional[str] = None
    auth: SMTPAuthConfig = Field(default_factory=SMTPAuthConfig)
    model_config = ConfigDict(extra="allow")


class Settings(BaseModel):
    """Aggregate runtime settings loaded from YAML."""

    smtp: SMTPConfig
    providers: Dict[str, Any]  # Type-specific provider configs
    reports: Dict[str, ReportConfig]
    credential_registry: Any = None  # CredentialRegistry instance
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    model_config = ConfigDict(extra="allow")

"""Typed configuration models for QueryHub."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class ProviderType(str, Enum):
    """Supported provider categories."""

    ADX = "adx"
    SQL = "sql"
    REST = "rest"
    CSV = "csv"


class CredentialType(str, Enum):
    """Credential types understood by core providers."""

    MANAGED_IDENTITY = "managed_identity"
    SERVICE_PRINCIPAL = "service_principal"
    USERNAME_PASSWORD = "username_password"  # nosec B105 - enum value, not a password
    CONNECTION_STRING = "connection_string"
    TOKEN = "token"  # nosec B105 - enum value, not a token
    NONE = "none"


class BaseCredentialConfig(BaseModel):
    """Base credential definition with common options."""

    type: CredentialType
    model_config = ConfigDict(extra="forbid")


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


class EmptyCredential(BaseCredentialConfig):
    type: Literal[CredentialType.NONE] = CredentialType.NONE


CredentialConfig = (
    ManagedIdentityCredential
    | ServicePrincipalCredential
    | UsernamePasswordCredential
    | ConnectionStringCredential
    | TokenCredential
    | EmptyCredential
)


class BaseProviderConfig(BaseModel):
    """Shared provider configuration attributes."""

    id: str
    type: ProviderType
    default_timeout_seconds: Optional[float] = Field(default=30.0, gt=0)
    retry_attempts: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=1.5, gt=0)
    credentials: Optional[CredentialConfig] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid")


class ADXProviderConfig(BaseProviderConfig):
    type: Literal[ProviderType.ADX] = ProviderType.ADX
    cluster_uri: str
    database: str
    client_request_id_prefix: Optional[str] = None


class SQLProviderTarget(BaseModel):
    """Normalised connection properties for SQL-style targets."""

    dsn: Optional[str] = None
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class SQLProviderConfig(BaseProviderConfig):
    type: Literal[ProviderType.SQL] = ProviderType.SQL
    target: SQLProviderTarget
    statement_options: Dict[str, Any] = Field(default_factory=dict)


class RESTProviderConfig(BaseProviderConfig):
    type: Literal[ProviderType.REST] = ProviderType.REST
    base_url: str
    default_headers: Dict[str, str] = Field(default_factory=dict)
    request_options: Dict[str, Any] = Field(default_factory=dict)


class CSVProviderConfig(BaseProviderConfig):
    type: Literal[ProviderType.CSV] = ProviderType.CSV
    root_path: str
    delimiter: str = ","
    encoding: str = "utf-8"


ProviderConfig = ADXProviderConfig | SQLProviderConfig | RESTProviderConfig | CSVProviderConfig


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
    providers: Dict[str, ProviderConfig]
    reports: Dict[str, ReportConfig]
    model_config = ConfigDict(extra="allow")

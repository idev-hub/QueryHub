"""New simplified provider models matching updated YAML structure.

The new YAML format has providers with resource configs:

providers:
  - id: adx_marketing
    resource:
      adx:
        cluster_uri: https://...
        database: Samples
    credentials: azure_default_credentials
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


# Resource Configs
class ADXResourceConfig(BaseModel):
    """Azure Data Explorer resource configuration."""

    cluster_uri: str
    database: str
    client_request_id_prefix: Optional[str] = None
    default_timeout_seconds: Optional[float] = Field(default=30.0, gt=0)
    retry_attempts: Optional[int] = Field(default=3, ge=0)
    model_config = ConfigDict(extra="allow")


class SQLResourceConfig(BaseModel):
    """SQL database resource configuration."""

    dsn: Optional[str] = None
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    default_timeout_seconds: Optional[float] = Field(default=30.0, gt=0)
    retry_attempts: Optional[int] = Field(default=3, ge=0)
    model_config = ConfigDict(extra="allow")


class RESTResourceConfig(BaseModel):
    """REST API resource configuration."""

    base_url: str
    default_headers: Dict[str, str] = Field(default_factory=dict)
    request_options: Dict[str, Any] = Field(default_factory=dict)
    default_timeout_seconds: Optional[float] = Field(default=30.0, gt=0)
    retry_attempts: Optional[int] = Field(default=3, ge=0)
    model_config = ConfigDict(extra="allow")


class CSVResourceConfig(BaseModel):
    """CSV file resource configuration."""

    root_path: str
    delimiter: str = ","
    encoding: str = "utf-8"
    model_config = ConfigDict(extra="allow")


# Provider Config with Resource
class ResourceConfig(BaseModel):
    """Resource configuration wrapper."""

    adx: Optional[ADXResourceConfig] = None
    sql: Optional[SQLResourceConfig] = None
    rest: Optional[RESTResourceConfig] = None
    csv: Optional[CSVResourceConfig] = None
    model_config = ConfigDict(extra="allow")

    def get_type(self) -> str:
        """Determine the resource type."""
        if self.adx:
            return "adx"
        elif self.sql:
            return "sql"
        elif self.rest:
            return "rest"
        elif self.csv:
            return "csv"
        else:
            raise ValueError("No resource configuration found")

    def get_config(
        self,
    ) -> ADXResourceConfig | SQLResourceConfig | RESTResourceConfig | CSVResourceConfig:
        """Get the actual resource configuration."""
        if self.adx:
            return self.adx
        elif self.sql:
            return self.sql
        elif self.rest:
            return self.rest
        elif self.csv:
            return self.csv
        else:
            raise ValueError("No resource configuration found")


class ProviderConfig(BaseModel):
    """Top-level provider configuration."""

    id: str
    resource: ResourceConfig
    credentials: Optional[str] = None  # Credential ID reference
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")

    @property
    def type(self) -> str:
        """Get provider type from resource config."""
        return self.resource.get_type()

    @property
    def default_timeout_seconds(self) -> float:
        """Get timeout from resource config."""
        config = self.resource.get_config()
        return getattr(config, "default_timeout_seconds", 30.0)

    @property
    def retry_attempts(self) -> int:
        """Get retry attempts from resource config."""
        config = self.resource.get_config()
        return getattr(config, "retry_attempts", 3)

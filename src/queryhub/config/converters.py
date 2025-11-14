"""Converter utilities to transform new config models to provider-specific configs."""

from __future__ import annotations

from typing import cast

from .provider_models import (
    ADXProviderConfig,
    ADXResourceConfig,
    CSVProviderConfig,
    CSVResourceConfig,
    ProviderConfig,
    RESTProviderConfig,
    RESTResourceConfig,
    SQLProviderConfig,
    SQLResourceConfig,
)


def convert_provider_config(
    config: ProviderConfig,
) -> ADXProviderConfig | SQLProviderConfig | RESTProviderConfig | CSVProviderConfig:
    """Convert generic ProviderConfig to type-specific config.

    This allows providers to continue using their specific config types
    while the loader works with the new unified format.

    Args:
        config: Generic provider configuration from YAML

    Returns:
        Type-specific provider configuration
    """
    resource_type = config.type
    resource_config = config.resource.get_config()

    if resource_type == "adx":
        adx_config = cast(ADXResourceConfig, resource_config)
        return ADXProviderConfig(
            id=config.id,
            type="adx",
            cluster_uri=adx_config.cluster_uri,
            database=adx_config.database,
            client_request_id_prefix=getattr(adx_config, "client_request_id_prefix", None),
            default_timeout_seconds=getattr(adx_config, "default_timeout_seconds", 30.0),
            retry_attempts=getattr(adx_config, "retry_attempts", 3),
            credentials=config.credentials,
            metadata=config.metadata,
        )
    elif resource_type == "sql":
        sql_config = cast(SQLResourceConfig, resource_config)
        return SQLProviderConfig(
            id=config.id,
            type="sql",
            target=sql_config,
            default_timeout_seconds=getattr(sql_config, "default_timeout_seconds", 30.0),
            retry_attempts=getattr(sql_config, "retry_attempts", 3),
            credentials=config.credentials,
            metadata=config.metadata,
        )
    elif resource_type == "rest":
        rest_config = cast(RESTResourceConfig, resource_config)
        return RESTProviderConfig(
            id=config.id,
            type="rest",
            base_url=rest_config.base_url,
            default_headers=rest_config.default_headers,
            request_options=rest_config.request_options,
            default_timeout_seconds=getattr(rest_config, "default_timeout_seconds", 30.0),
            retry_attempts=getattr(rest_config, "retry_attempts", 3),
            credentials=config.credentials,
            metadata=config.metadata,
        )
    elif resource_type == "csv":
        csv_config = cast(CSVResourceConfig, resource_config)
        return CSVProviderConfig(
            id=config.id,
            type="csv",
            root_path=csv_config.root_path,
            delimiter=csv_config.delimiter,
            encoding=csv_config.encoding,
            credentials=config.credentials,
            metadata=config.metadata,
        )
    else:
        raise ValueError(f"Unsupported provider type: {resource_type}")

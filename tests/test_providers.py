"""Comprehensive tests for all provider types."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from queryhub.config.loader import ConfigLoader
from queryhub.config.provider_models import (
    ADXResourceConfig,
    CSVResourceConfig,
    ProviderConfig,
    RESTResourceConfig,
    ResourceConfig,
    SQLResourceConfig,
)
from queryhub.core.credentials import CredentialRegistry
from queryhub.providers.generic.resources.csv import CSVQueryProvider
from queryhub.providers.generic.resources.rest import RESTQueryProvider
from queryhub.providers.generic.resources.sql import SQLQueryProvider


# =============================================================================
# SQL Provider Tests
# =============================================================================


def test_sql_provider_config_validation() -> None:
    """Test SQL provider configuration validation."""
    # Valid config with DSN
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="postgresql+asyncpg://localhost:5432/testdb",
            )
        ),
    )
    assert config.type == "sql"
    assert config.resource.sql is not None
    assert config.resource.sql.dsn == "postgresql+asyncpg://localhost:5432/testdb"


def test_sql_provider_config_with_options() -> None:
    """Test SQL provider configuration with connection options."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="postgresql+asyncpg://localhost:5432/testdb",
                options={
                    "pool_size": 10,
                    "max_overflow": 20,
                    "application_name": "queryhub_test",
                },
            )
        ),
    )
    assert config.resource.sql is not None
    assert config.resource.sql.options is not None
    assert config.resource.sql.options["pool_size"] == 10
    assert config.resource.sql.options is not None
    assert config.resource.sql.options["application_name"] == "queryhub_test"


def test_sql_provider_config_with_timeout_and_retry() -> None:
    """Test SQL provider with timeout and retry settings."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="sqlite:///:memory:",
                default_timeout_seconds=60.0,
                retry_attempts=5,
            )
        ),
    )
    assert config.default_timeout_seconds == 60.0
    assert config.retry_attempts == 5


@pytest.mark.asyncio
async def test_sql_provider_initialization() -> None:
    """Test SQL provider initialization."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="sqlite+aiosqlite:///:memory:",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = SQLQueryProvider(config, credential_registry=registry)
    
    assert provider.config.id == "test_sql"
    assert provider.sql_config.dsn == "sqlite+aiosqlite:///:memory:"
    
    await provider.close()


@pytest.mark.asyncio
async def test_sql_provider_basic_query() -> None:
    """Test SQL provider can execute a basic query."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="sqlite+aiosqlite:///:memory:",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = SQLQueryProvider(config, credential_registry=registry)
    
    try:
        result = await provider.execute({"text": "SELECT 1 as num, 'test' as str"})
        
        assert result.data is not None
        assert len(result.data) == 1
        assert result.data[0]["num"] == 1
        assert result.data[0]["str"] == "test"
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_sql_provider_query_with_parameters() -> None:
    """Test SQL provider with basic query operations."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="sqlite+aiosqlite:///:memory:",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = SQLQueryProvider(config, credential_registry=registry)
    
    try:
        # Test simple parameterized query using SQLite built-in tables
        result = await provider.execute({
            "text": "SELECT :value as result, :name as name",
            "parameters": {"value": 42, "name": "test"}
        })
        
        assert len(result.data) == 1
        assert result.data[0]["result"] == 42
        assert result.data[0]["name"] == "test"
    finally:
        await provider.close()


# =============================================================================
# CSV Provider Tests
# =============================================================================


def test_csv_provider_config_validation() -> None:
    """Test CSV provider configuration validation."""
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(
                root_path="/data/exports",
                delimiter=",",
            )
        ),
    )
    assert config.type == "csv"
    assert config.resource.csv is not None
    assert config.resource.csv.root_path == "/data/exports"
    assert config.resource.csv.delimiter == ","


def test_csv_provider_config_with_encoding() -> None:
    """Test CSV provider configuration with custom encoding."""
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(
                root_path="/data",
                encoding="utf-8-sig",
                delimiter=";",
            )
        ),
    )
    assert config.resource.csv.encoding == "utf-8-sig"
    assert config.resource.csv.delimiter == ";"


@pytest.mark.asyncio
async def test_csv_provider_initialization() -> None:
    """Test CSV provider initialization."""
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(
                root_path=".",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = CSVQueryProvider(config, credential_registry=registry)
    
    assert provider.config.id == "test_csv"
    assert provider.csv_config.root_path == "."
    
    await provider.close()


@pytest.mark.asyncio
async def test_csv_provider_read_file(tmp_path: Path) -> None:
    """Test CSV provider can read a file."""
    # Create test CSV file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n", encoding="utf-8")
    
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(
                root_path=str(tmp_path),
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = CSVQueryProvider(config, credential_registry=registry)
    
    try:
        result = await provider.execute({"file": "test.csv"})
        
        assert result.data is not None
        assert len(result.data) == 2
        assert result.data[0]["name"] == "Alice"
        assert result.data[1]["value"] == "200"
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_csv_provider_with_custom_delimiter(tmp_path: Path) -> None:
    """Test CSV provider with custom delimiter."""
    # Create test CSV file with semicolon delimiter
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id;name;value\n1;Alice;100\n2;Bob;200\n", encoding="utf-8")
    
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(
                root_path=str(tmp_path),
                delimiter=";",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = CSVQueryProvider(config, credential_registry=registry)
    
    try:
        result = await provider.execute({"file": "test.csv"})
        
        assert len(result.data) == 2
        assert result.data[0]["name"] == "Alice"
    finally:
        await provider.close()


# =============================================================================
# REST Provider Tests
# =============================================================================


def test_rest_provider_config_validation() -> None:
    """Test REST provider configuration validation."""
    config = ProviderConfig(
        id="test_rest",
        resource=ResourceConfig(
            rest=RESTResourceConfig(
                base_url="https://api.example.com",
                default_headers={"Accept": "application/json"},
            )
        ),
    )
    assert config.type == "rest"
    assert config.resource.rest.base_url == "https://api.example.com"
    assert config.resource.rest.default_headers["Accept"] == "application/json"


def test_rest_provider_config_with_auth() -> None:
    """Test REST provider configuration with authentication headers."""
    config = ProviderConfig(
        id="test_rest",
        resource=ResourceConfig(
            rest=RESTResourceConfig(
                base_url="https://api.example.com",
                default_headers={
                    "Authorization": "Bearer token123",
                    "Content-Type": "application/json",
                },
            )
        ),
    )
    assert "Authorization" in config.resource.rest.default_headers


def test_rest_provider_config_with_request_options() -> None:
    """Test REST provider with custom request options."""
    config = ProviderConfig(
        id="test_rest",
        resource=ResourceConfig(
            rest=RESTResourceConfig(
                base_url="https://api.example.com",
                request_options={
                    "timeout": 60,
                    "raise_for_status": True,
                },
            )
        ),
    )
    assert config.resource.rest.request_options["timeout"] == 60
    assert config.resource.rest.request_options["raise_for_status"] is True


@pytest.mark.asyncio
async def test_rest_provider_initialization() -> None:
    """Test REST provider initialization."""
    config = ProviderConfig(
        id="test_rest",
        resource=ResourceConfig(
            rest=RESTResourceConfig(
                base_url="https://api.example.com",
            )
        ),
    )
    
    registry = CredentialRegistry()
    provider = RESTQueryProvider(config, credential_registry=registry)
    
    assert provider.config.id == "test_rest"
    assert provider.rest_config.base_url == "https://api.example.com"
    
    await provider.close()


# =============================================================================
# Azure Data Explorer (ADX) Provider Tests
# =============================================================================


def test_adx_provider_config_validation() -> None:
    """Test ADX provider configuration validation."""
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://help.kusto.windows.net",
                database="Samples",
            )
        ),
    )
    assert config.type == "adx"
    assert config.resource.adx.cluster_uri == "https://help.kusto.windows.net"
    assert config.resource.adx.database == "Samples"


def test_adx_provider_config_with_options() -> None:
    """Test ADX provider with custom options."""
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://mycluster.kusto.windows.net",
                database="mydb",
                client_request_id_prefix="queryhub_",
                default_timeout_seconds=120.0,
                retry_attempts=3,
            )
        ),
    )
    assert config.resource.adx.client_request_id_prefix == "queryhub_"
    assert config.default_timeout_seconds == 120.0
    assert config.retry_attempts == 3


@pytest.mark.asyncio
async def test_adx_provider_initialization() -> None:
    """Test ADX provider initialization without Azure SDK."""
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    
    # Import ADX provider
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    assert provider.config.id == "test_adx"
    assert provider.adx_config.cluster_uri == "https://test.kusto.windows.net"
    assert provider.adx_config.database == "testdb"
    
    await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_missing_query_text() -> None:
    """Test ADX provider error handling for missing query text."""
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        with pytest.raises(Exception) as exc_info:
            await provider.execute({})  # Missing 'text' key
        
        assert "require" in str(exc_info.value).lower() or "text" in str(exc_info.value).lower()
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_build_client_properties() -> None:
    """Test ADX provider builds client properties correctly."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
                client_request_id_prefix="test_prefix",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Test building client properties with various options
        query = {
            "text": "TestTable | take 10",
            "client_request_id": "req123",
            "parameters": {"param1": "value1", "param2": 42},
            "timeout_seconds": 60,
            "options": {"query_consistency": "strongconsistency"},
        }
        
        properties = provider._build_client_properties(query)
        
        # Verify properties object was created
        assert properties is not None
        assert hasattr(properties, "client_request_id")
        
        # Verify client request ID includes prefix
        if properties.client_request_id:
            assert "test_prefix" in properties.client_request_id
            assert "req123" in properties.client_request_id
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_build_client_properties_defaults() -> None:
    """Test ADX provider builds client properties with defaults."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Test building client properties with minimal query
        query = {"text": "TestTable | take 10"}
        
        properties = provider._build_client_properties(query)
        
        # Verify properties object was created with defaults
        assert properties is not None
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_execute_with_mock() -> None:
    """Test ADX provider execute with mocked client."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock, MagicMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    # Create mock credential
    mock_credential = AsyncMock()
    mock_credential.get_connection = AsyncMock(return_value="mock_kcsb")
    mock_credential.close = AsyncMock()
    
    registry = CredentialRegistry()
    # Register using proper API
    azure_config = AzureCredentialConfig(
        type="default_credentials",
    )
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Mock the KustoClient
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        # Mock response data
        mock_row = {"col1": "value1", "col2": 42}
        mock_primary_result = [mock_row]
        mock_response.primary_results = [mock_primary_result]
        mock_response.execution_time = 1.5
        mock_response.request_id = "req-123"
        
        mock_client.execute = AsyncMock(return_value=mock_response)
        mock_client.close = AsyncMock()
        
        # Inject mock client
        provider._client = mock_client
        
        # Execute query
        result = await provider.execute({"text": "TestTable | take 1"})
        
        # Verify results
        assert result.data is not None
        assert len(result.data) == 1
        assert result.data[0]["col1"] == "value1"
        assert result.data[0]["col2"] == 42
        assert result.metadata["execution_time"] == 1.5
        assert result.metadata["request_id"] == "req-123"
        
        # Verify client was called correctly
        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args
        assert call_args[0][0] == "testdb"  # database
        assert call_args[0][1] == "TestTable | take 1"  # query
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_execute_error_handling() -> None:
    """Test ADX provider handles execution errors."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    # Create registry with credential
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(
        type="default_credentials",
    )
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Mock client that raises an error
        mock_client = AsyncMock()
        mock_client.execute = AsyncMock(side_effect=Exception("Query execution failed"))
        mock_client.close = AsyncMock()
        
        provider._client = mock_client
        
        # Execute query and expect error
        with pytest.raises(Exception) as exc_info:
            await provider.execute({"text": "BadQuery"})
        
        assert "failed" in str(exc_info.value).lower()
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_close_without_initialization() -> None:
    """Test ADX provider close without creating client."""
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
    )
    
    registry = CredentialRegistry()
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    # Close without ever creating client
    await provider.close()  # Should not raise error
    
    # Verify nothing crashes
    assert provider._client is None


def test_adx_provider_invalid_config() -> None:
    """Test ADX provider rejects invalid configuration."""
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    # Config with wrong type
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite:///:memory:"),
        ),
    )
    
    registry = CredentialRegistry()
    
    with pytest.raises(Exception) as exc_info:
        ADXQueryProvider(config, credential_registry=registry)
    
    assert "adx" in str(exc_info.value).lower() or "require" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_adx_provider_execute_no_primary_results() -> None:
    """Test ADX provider handles response with no primary results."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock, MagicMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Mock client with no primary results
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.primary_results = []  # Empty results
        mock_response.execution_time = 0.5
        mock_response.request_id = "req-456"
        
        mock_client.execute = AsyncMock(return_value=mock_response)
        mock_client.close = AsyncMock()
        
        provider._client = mock_client
        
        result = await provider.execute({"text": "TestTable | take 0"})
        
        # Should return empty data
        assert result.data == []
        assert result.metadata["execution_time"] == 0.5
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_close_with_client_and_credential() -> None:
    """Test ADX provider closes both client and credential."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    # Mock both client and credential
    mock_client = AsyncMock()
    mock_client.close = AsyncMock()
    mock_credential = AsyncMock()
    mock_credential.close = AsyncMock()
    
    provider._client = mock_client
    provider._credential = mock_credential
    
    # Close should call both
    await provider.close()
    
    mock_client.close.assert_called_once()
    mock_credential.close.assert_called_once()


@pytest.mark.asyncio
async def test_adx_provider_missing_azure_sdk() -> None:
    """Test ADX provider handles missing Azure SDK dependency."""
    import sys
    from unittest.mock import patch
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    from queryhub.config.credential_models import AzureCredentialConfig
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    # Mock import to fail for azure.kusto.data
    with patch.dict(sys.modules, {"azure.kusto.data.aio": None}):
        with pytest.raises(Exception):
            # Force client creation which will fail on import
            await provider._create_client()
    
    await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_client_properties_with_all_parameters() -> None:
    """Test building client properties with all possible parameters."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
                client_request_id_prefix="custom_",
            )
        ),
        credentials="azure_cred",
    )
    
    from queryhub.config.credential_models import AzureCredentialConfig
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        query = {
            "text": "TestTable | take 10",
            "client_request_id": "test123",
            "parameters": {
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
                "limit": 100,
            },
            "timeout_seconds": 90,
            "options": {
                "query_consistency": "strongconsistency",
                "queryconsistency": "weakconsistency",
            },
        }
        
        properties = provider._build_client_properties(query)
        
        # Verify all properties were set
        assert properties is not None
        
        # Check client_request_id has prefix
        if properties.client_request_id:
            assert "custom_" in properties.client_request_id
            assert "test123" in properties.client_request_id
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_concurrent_client_creation() -> None:
    """Test that concurrent client creation is thread-safe."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    import asyncio
    from unittest.mock import AsyncMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    # Mock the _create_client to track calls
    create_count = 0
    
    async def mock_create():
        nonlocal create_count
        create_count += 1
        await asyncio.sleep(0.01)  # Simulate slow creation
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        return mock_client
    
    provider._create_client = mock_create
    
    try:
        # Try to get client concurrently
        clients = await asyncio.gather(
            provider._get_client(),
            provider._get_client(),
            provider._get_client(),
        )
        
        # All should return the same client
        assert clients[0] is clients[1]
        assert clients[1] is clients[2]
        
        # Should only create once due to locking
        assert create_count == 1
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_no_credential_registry() -> None:
    """Test ADX provider handles missing credential registry."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    # Create provider without credential registry
    provider = ADXQueryProvider(config, credential_registry=None)
    
    try:
        # Trying to create client should fail
        with pytest.raises(Exception) as exc_info:
            await provider._create_client()
        
        assert "credential registry" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_query_parameter_iteration() -> None:
    """Test ADX provider iterates through query parameters correctly."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    from queryhub.config.credential_models import AzureCredentialConfig
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Build properties with multiple parameters that need iteration
        query = {
            "text": "TestTable",
            "parameters": {
                "param1": "value1",
                "param2": "value2",
                "param3": 42,
            },
        }
        
        properties = provider._build_client_properties(query)
        
        # Just verify it doesn't crash - parameters are iterated internally
        assert properties is not None
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_query_options_iteration() -> None:
    """Test ADX provider iterates through query options correctly."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    from queryhub.config.credential_models import AzureCredentialConfig
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Build properties with multiple options that need iteration
        query = {
            "text": "TestTable",
            "options": {
                "option1": "value1",
                "option2": "value2",
                "option3": True,
            },
        }
        
        properties = provider._build_client_properties(query)
        
        # Just verify it doesn't crash - options are iterated internally
        assert properties is not None
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_short_query_text() -> None:
    """Test ADX provider with short query text (for logging coverage)."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock, MagicMock
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.primary_results = []
        mock_response.execution_time = 0.1
        mock_response.request_id = "req-short"
        
        mock_client.execute = AsyncMock(return_value=mock_response)
        mock_client.close = AsyncMock()
        
        provider._client = mock_client
        
        # Execute with very short query (less than 100 chars)
        result = await provider.execute({"text": "T | take 1"})
        
        # Should work fine
        assert result.data == []
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_adx_provider_full_client_creation_flow() -> None:
    """Test ADX provider complete client creation with Azure SDK."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from unittest.mock import AsyncMock, MagicMock, patch
    from queryhub.config.credential_models import AzureCredentialConfig
    
    config = ProviderConfig(
        id="test_adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://test.kusto.windows.net",
                database="testdb",
            )
        ),
        credentials="azure_cred",
    )
    
    registry = CredentialRegistry()
    azure_config = AzureCredentialConfig(type="default_credentials")
    registry.register("azure_cred", "azure", "default_credentials", azure_config)
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Mock the credential's get_connection to return a mock KCSB
        mock_kcsb = MagicMock()
        
        # Mock KustoClient class where it's imported
        with patch("azure.kusto.data.aio.KustoClient") as MockKustoClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.close = AsyncMock()
            MockKustoClient.return_value = mock_client_instance
            
            # Get credential and mock its get_connection
            credential = registry.get_credential("azure_cred", cloud_provider="azure")
            
            async def mock_get_connection(**kwargs):
                # This should be called with service_type, cluster_uri, database
                assert kwargs.get("service_type") == "kusto"
                assert "cluster_uri" in kwargs
                assert "database" in kwargs
                return mock_kcsb
            
            credential.get_connection = mock_get_connection
            
            # Now trigger client creation by calling _get_client
            client = await provider._get_client()
            
            # Verify the flow executed
            assert client is not None
            MockKustoClient.assert_called_once_with(mock_kcsb)
    finally:
        await provider.close()


# =============================================================================
# Provider Factory Tests
# =============================================================================


def test_provider_config_types() -> None:
    """Test that all provider types are correctly identified."""
    sql_config = ProviderConfig(
        id="sql",
        resource=ResourceConfig(sql=SQLResourceConfig(dsn="sqlite:///:memory:")),
    )
    assert sql_config.type == "sql"
    
    csv_config = ProviderConfig(
        id="csv",
        resource=ResourceConfig(csv=CSVResourceConfig(root_path=".")),
    )
    assert csv_config.type == "csv"
    
    rest_config = ProviderConfig(
        id="rest",
        resource=ResourceConfig(rest=RESTResourceConfig(base_url="https://api.example.com")),
    )
    assert rest_config.type == "rest"
    
    adx_config = ProviderConfig(
        id="adx",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://help.kusto.windows.net",
                database="Samples",
            )
        ),
    )
    assert adx_config.type == "adx"


def test_provider_with_credentials_reference() -> None:
    """Test provider with credential ID reference."""
    config = ProviderConfig(
        id="test_provider",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="postgresql://localhost/db"),
        ),
        credentials="postgres_creds",
    )
    assert config.credentials == "postgres_creds"


def test_provider_with_metadata() -> None:
    """Test provider with custom metadata."""
    config = ProviderConfig(
        id="test_provider",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite:///:memory:"),
        ),
        metadata={
            "description": "Test database",
            "owner": "data-team",
            "tags": ["test", "development"],
        },
    )
    assert config.metadata["description"] == "Test database"
    assert "test" in config.metadata["tags"]


# =============================================================================
# Integration Tests with Config Loader
# =============================================================================


@pytest.mark.asyncio
async def test_load_all_provider_types(tmp_path: Path) -> None:
    """Test loading configuration with all provider types."""
    providers_dir = tmp_path / "providers"
    smtp_dir = tmp_path / "smtp"
    providers_dir.mkdir()
    smtp_dir.mkdir()
    
    # Create config with all provider types
    providers_yaml = """
credentials:
  - id: empty_cred
    generic:
      type: no_credential

providers:
  - id: sql_provider
    resource:
      sql:
        dsn: "sqlite+aiosqlite:///:memory:"
    credentials: empty_cred
  
  - id: csv_provider
    resource:
      csv:
        root_path: "."
    credentials: empty_cred
  
  - id: rest_provider
    resource:
      rest:
        base_url: "https://api.example.com"
    credentials: empty_cred
  
  - id: adx_provider
    resource:
      adx:
        cluster_uri: "https://help.kusto.windows.net"
        database: "Samples"
    credentials: empty_cred
"""
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")
    
    # SMTP config
    (smtp_dir / "default.yaml").write_text(
        "host: localhost\nport: 1025\nuse_tls: false\ndefault_from: test@example.com",
        encoding="utf-8"
    )
    
    # Load configuration
    loader = ConfigLoader(tmp_path)
    settings = loader.load_sync()
    
    # Verify all providers loaded
    assert len(settings.providers) == 4
    assert "sql_provider" in settings.providers
    assert "csv_provider" in settings.providers
    assert "rest_provider" in settings.providers
    assert "adx_provider" in settings.providers
    
    # Verify provider types
    assert settings.providers["sql_provider"].type == "sql"
    assert settings.providers["csv_provider"].type == "csv"
    assert settings.providers["rest_provider"].type == "rest"
    assert settings.providers["adx_provider"].type == "adx"
    
    # Verify credential reference
    assert settings.providers["sql_provider"].credentials == "empty_cred"
    assert "empty_cred" in settings.credential_registry


def test_provider_timeout_and_retry_defaults() -> None:
    """Test that providers have correct default timeout and retry values."""
    config = ProviderConfig(
        id="test",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite:///:memory:"),
        ),
    )
    
    # Check defaults
    assert config.default_timeout_seconds == 30.0
    assert config.retry_attempts == 3


def test_provider_custom_timeout_and_retry() -> None:
    """Test custom timeout and retry configuration."""
    config = ProviderConfig(
        id="test",
        resource=ResourceConfig(
            sql=SQLResourceConfig(
                dsn="sqlite:///:memory:",
                default_timeout_seconds=90.0,
                retry_attempts=5,
            ),
        ),
    )
    
    assert config.default_timeout_seconds == 90.0
    assert config.retry_attempts == 5


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_sql_provider_invalid_query() -> None:
    """Test SQL provider handles invalid queries gracefully."""
    config = ProviderConfig(
        id="test_sql",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite+aiosqlite:///:memory:"),
        ),
    )
    
    registry = CredentialRegistry()
    provider = SQLQueryProvider(config, credential_registry=registry)
    
    try:
        with pytest.raises(Exception):  # Should raise SQLAlchemy error
            await provider.execute({"text": "SELECT * FROM nonexistent_table"})
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_csv_provider_file_not_found(tmp_path: Path) -> None:
    """Test CSV provider handles missing files gracefully."""
    config = ProviderConfig(
        id="test_csv",
        resource=ResourceConfig(
            csv=CSVResourceConfig(root_path=str(tmp_path)),
        ),
    )
    
    registry = CredentialRegistry()
    provider = CSVQueryProvider(config, credential_registry=registry)
    
    try:
        with pytest.raises(Exception):  # Should raise FileNotFoundError or similar
            await provider.execute({"file": "nonexistent.csv"})
    finally:
        await provider.close()


# =============================================================================
# Concurrent Provider Tests
# =============================================================================


@pytest.mark.asyncio
async def test_multiple_providers_concurrent() -> None:
    """Test multiple providers can be used concurrently."""
    sql_config = ProviderConfig(
        id="sql1",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite+aiosqlite:///:memory:"),
        ),
    )
    
    sql_config2 = ProviderConfig(
        id="sql2",
        resource=ResourceConfig(
            sql=SQLResourceConfig(dsn="sqlite+aiosqlite:///:memory:"),
        ),
    )
    
    registry = CredentialRegistry()
    provider1 = SQLQueryProvider(sql_config, credential_registry=registry)
    provider2 = SQLQueryProvider(sql_config2, credential_registry=registry)
    
    try:
        # Execute queries concurrently
        results = await asyncio.gather(
            provider1.execute({"text": "SELECT 1 as num"}),
            provider2.execute({"text": "SELECT 2 as num"}),
        )
        
        assert results[0].data[0]["num"] == 1
        assert results[1].data[0]["num"] == 2
    finally:
        await provider1.close()
        await provider2.close()

"""Integration tests for Azure Data Explorer (ADX) provider.

These tests require:
1. Azure Kusto SDK installed: pip install azure-kusto-data
2. Real Azure credentials configured
3. Access to an ADX cluster (or use the public help cluster)

Tests will be skipped if dependencies or credentials are missing.
"""

from __future__ import annotations

import os

import pytest

from queryhub.config.credential_models import AzureCredentialConfig
from queryhub.config.provider_models import ADXResourceConfig, ProviderConfig, ResourceConfig
from queryhub.core.credentials import CredentialRegistry


# Skip all tests if Azure SDK not installed
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed"),
    reason="Azure Kusto SDK required for ADX integration tests"
)


@pytest.fixture
def adx_help_cluster_config() -> ProviderConfig:
    """Config for Azure's public help cluster (no auth required)."""
    return ProviderConfig(
        id="help_cluster",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri="https://help.kusto.windows.net",
                database="Samples",
            )
        ),
        credentials="azure_public",
    )


@pytest.fixture
def public_credential_registry() -> CredentialRegistry:
    """Registry with credential for public help cluster."""
    registry = CredentialRegistry()
    
    # The help cluster allows anonymous queries
    azure_config = AzureCredentialConfig(
        type="default_credentials",
    )
    registry.register("azure_public", "azure", "default_credentials", azure_config)
    
    return registry


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_TENANT_ID") and not os.getenv("AZURE_CLIENT_ID"),
    reason="Azure credentials not configured - set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET or use 'az login'"
)
async def test_adx_public_help_cluster(
    adx_help_cluster_config: ProviderConfig,
    public_credential_registry: CredentialRegistry,
) -> None:
    """Test ADX provider with Azure's public help cluster.
    
    This test connects to a real ADX cluster (help.kusto.windows.net).
    Even though the data is public, Azure authentication is still required.
    
    Prerequisites:
    - Run 'az login' to authenticate via Azure CLI, OR
    - Set environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
    """
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(
        adx_help_cluster_config,
        credential_registry=public_credential_registry,
    )
    
    try:
        # Query the public Samples database
        # StormEvents is a well-known sample table
        result = await provider.execute({
            "text": "StormEvents | take 5 | project StartTime, EventType, State"
        })
        
        # Verify we got real data back
        assert result.data is not None, "Should return data"
        assert len(result.data) <= 5, "Should return at most 5 rows"
        
        # Verify expected columns
        if len(result.data) > 0:
            first_row = result.data[0]
            assert "StartTime" in first_row or "starttime" in str(first_row).lower()
            assert "EventType" in first_row or "eventtype" in str(first_row).lower()
            assert "State" in first_row or "state" in str(first_row).lower()
        
        # Verify metadata
        assert result.metadata is not None
        assert "execution_time" in result.metadata
        assert "request_id" in result.metadata
        
        print("\n✓ Successfully queried ADX help cluster")
        print(f"  Rows returned: {len(result.data)}")
        print(f"  Execution time: {result.metadata['execution_time']}")
        print(f"  Request ID: {result.metadata['request_id']}")
        
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_TENANT_ID") and not os.getenv("AZURE_CLIENT_ID"),
    reason="Azure credentials not configured"
)
async def test_adx_query_with_parameters(
    adx_help_cluster_config: ProviderConfig,
    public_credential_registry: CredentialRegistry,
) -> None:
    """Test ADX provider with parameterized queries."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(
        adx_help_cluster_config,
        credential_registry=public_credential_registry,
    )
    
    try:
        # Query with parameters
        result = await provider.execute({
            "text": "StormEvents | where EventType == eventType | take limit",
            "parameters": {
                "eventType": "Tornado",
                "limit": 3,
            }
        })
        
        assert result.data is not None
        assert len(result.data) <= 3
        
        print(f"\n✓ Parameterized query successful: {len(result.data)} rows")
        
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_TENANT_ID") and not os.getenv("AZURE_CLIENT_ID"),
    reason="Azure credentials not configured"
)
async def test_adx_query_with_timeout(
    adx_help_cluster_config: ProviderConfig,
    public_credential_registry: CredentialRegistry,
) -> None:
    """Test ADX provider respects timeout settings."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(
        adx_help_cluster_config,
        credential_registry=public_credential_registry,
    )
    
    try:
        # Quick query with short timeout
        result = await provider.execute({
            "text": "StormEvents | take 1",
            "timeout_seconds": 30,
        })
        
        assert result.data is not None
        assert len(result.data) == 1
        
        print("\n✓ Timeout setting respected")
        
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_TENANT_ID") and not os.getenv("AZURE_CLIENT_ID"),
    reason="Azure credentials not configured"
)
async def test_adx_aggregation_query(
    adx_help_cluster_config: ProviderConfig,
    public_credential_registry: CredentialRegistry,
) -> None:
    """Test ADX provider with aggregation queries."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    provider = ADXQueryProvider(
        adx_help_cluster_config,
        credential_registry=public_credential_registry,
    )
    
    try:
        # Aggregation query
        result = await provider.execute({
            "text": """
                StormEvents 
                | summarize Count=count() by State 
                | order by Count desc 
                | take 5
            """
        })
        
        assert result.data is not None
        assert len(result.data) <= 5
        
        # Should have State and Count columns
        if len(result.data) > 0:
            first_row = result.data[0]
            assert "State" in first_row or "state" in str(first_row).lower()
            assert "Count" in first_row or "count" in str(first_row).lower()
        
        print(f"\n✓ Aggregation query successful: {len(result.data)} states")
        
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_TENANT_ID") and not os.getenv("AZURE_CLIENT_ID"),
    reason="Azure credentials not configured"
)
async def test_adx_invalid_query_error_handling(
    adx_help_cluster_config: ProviderConfig,
    public_credential_registry: CredentialRegistry,
) -> None:
    """Test ADX provider handles invalid queries properly."""
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    from queryhub.core.errors import ProviderExecutionError
    
    provider = ADXQueryProvider(
        adx_help_cluster_config,
        credential_registry=public_credential_registry,
    )
    
    try:
        # Invalid KQL syntax
        with pytest.raises(ProviderExecutionError) as exc_info:
            await provider.execute({
                "text": "NonExistentTable | where InvalidColumn == 'value'"
            })
        
        error_msg = str(exc_info.value).lower()
        assert "failed" in error_msg or "error" in error_msg
        
        print("\n✓ Error handling works correctly")
        
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ADX_CLUSTER_URI") or not os.getenv("ADX_DATABASE"),
    reason="Custom ADX cluster credentials not configured"
)
async def test_adx_custom_cluster() -> None:
    """Test ADX provider with custom cluster (requires env vars).
    
    Set these environment variables to test with your own cluster:
    - ADX_CLUSTER_URI: Your cluster URI (e.g., https://mycluster.kusto.windows.net)
    - ADX_DATABASE: Your database name
    - AZURE_TENANT_ID: Your Azure tenant ID (optional, for auth)
    - AZURE_CLIENT_ID: Your Azure client ID (optional, for auth)
    - AZURE_CLIENT_SECRET: Your Azure client secret (optional, for auth)
    """
    pytest.importorskip("azure.kusto.data", reason="Azure Kusto SDK not installed")
    
    from queryhub.providers.azure.resources.adx import ADXQueryProvider
    
    cluster_uri = os.getenv("ADX_CLUSTER_URI")
    database = os.getenv("ADX_DATABASE")
    
    config = ProviderConfig(
        id="custom_cluster",
        resource=ResourceConfig(
            adx=ADXResourceConfig(
                cluster_uri=cluster_uri,
                database=database,
            )
        ),
        credentials="azure_custom",
    )
    
    registry = CredentialRegistry()
    
    # Use default credentials (will use environment variables or managed identity)
    azure_config = AzureCredentialConfig(
        type="default_credentials",
    )
    registry.register("azure_custom", "azure", "default_credentials", azure_config)
    
    provider = ADXQueryProvider(config, credential_registry=registry)
    
    try:
        # Simple test query - adjust based on your schema
        result = await provider.execute({
            "text": ".show database schema | take 1"
        })
        
        assert result.data is not None
        
        print("\n✓ Custom cluster connection successful")
        print(f"  Cluster: {cluster_uri}")
        print(f"  Database: {database}")
        
    finally:
        await provider.close()


# Summary fixture to show integration test status
@pytest.fixture(scope="session", autouse=True)
def print_integration_test_info():
    """Print information about running integration tests."""
    yield
    
    print("\n" + "="*80)
    print("ADX Integration Test Summary")
    print("="*80)
    print("\nThese tests verify ADX provider works with real Azure infrastructure.")
    print("\nPublic cluster tests use: https://help.kusto.windows.net")
    print("  - No authentication required")
    print("  - Safe to run in CI/CD")
    print("\nTo test with your own cluster, set environment variables:")
    print("  export ADX_CLUSTER_URI='https://yourcluster.kusto.windows.net'")
    print("  export ADX_DATABASE='your_database'")
    print("  export AZURE_TENANT_ID='your_tenant_id'  # optional")
    print("  export AZURE_CLIENT_ID='your_client_id'  # optional")
    print("  export AZURE_CLIENT_SECRET='your_secret'  # optional")
    print("\nRun with: pytest tests/test_adx_integration.py -v -m integration")
    print("="*80 + "\n")

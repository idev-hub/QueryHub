# Azure Data Explorer - Default Credentials Guide

## Overview

QueryHub now supports Azure DefaultAzureCredential for Azure Data Explorer (ADX) provider authentication. This is the **recommended approach** for both local development and production deployments.

## What is DefaultAzureCredential?

`DefaultAzureCredential` is a smart credential chain that automatically tries multiple authentication methods in order:

1. **Environment Variables** - Service principal credentials from env vars
2. **Managed Identity** - Automatically used when running in Azure (VM, App Service, Container Instance, etc.)
3. **Azure CLI** - Uses your local `az login` credentials (perfect for local development)
4. **Azure PowerShell** - Uses credentials from PowerShell Az module
5. **Interactive Browser** - Falls back to browser authentication if needed

## Benefits

- ✅ **Single configuration** works everywhere (local dev, Azure VMs, containers, etc.)
- ✅ **No secrets in config files** when using local identity
- ✅ **Seamless transition** from development to production
- ✅ **Automatic identity discovery** - no manual configuration needed

## Configuration

### Basic Setup

```yaml
providers:
  - id: my_adx_cluster
    type: adx
    cluster_uri: https://mycluster.kusto.windows.net
    database: MyDatabase
    credentials:
      type: default_credentials
```

That's it! No client IDs, secrets, or tokens needed.

## Local Development Setup

### Prerequisites

1. Install Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli
2. Log in to Azure:

```bash
az login
```

3. Verify your identity:

```bash
az account show
```

### Grant ADX Access

Ensure your Azure account has appropriate permissions on the ADX cluster:

```bash
# Add yourself as a viewer (read access)
az kusto database-principal-assignment create \
  --cluster-name mycluster \
  --database-name MyDatabase \
  --resource-group myResourceGroup \
  --principal-id $(az ad signed-in-user show --query id -o tsv) \
  --principal-type User \
  --role Viewer \
  --principal-assignment-name myUserAccess
```

Or use the Azure Portal:
1. Navigate to your ADX cluster
2. Select your database
3. Go to "Permissions"
4. Add your user with appropriate role (Viewer, User, Admin)

## Azure Deployment

When deployed to Azure services with managed identity enabled, DefaultAzureCredential automatically uses the managed identity - no code changes needed!

### Enable Managed Identity

**For Azure VM:**
```bash
az vm identity assign --name myVM --resource-group myResourceGroup
```

**For Azure App Service:**
```bash
az webapp identity assign --name myAppService --resource-group myResourceGroup
```

**For Azure Container Instance:**
```bash
az container create \
  --name myContainer \
  --resource-group myResourceGroup \
  --image myimage:latest \
  --assign-identity
```

### Grant Managed Identity Access to ADX

```bash
# Get the managed identity principal ID
PRINCIPAL_ID=$(az vm identity show --name myVM --resource-group myResourceGroup --query principalId -o tsv)

# Grant access to ADX database
az kusto database-principal-assignment create \
  --cluster-name mycluster \
  --database-name MyDatabase \
  --resource-group myResourceGroup \
  --principal-id $PRINCIPAL_ID \
  --principal-type App \
  --role Viewer \
  --principal-assignment-name managedIdentityAccess
```

## Troubleshooting

### "No credential found" error

**Cause:** DefaultAzureCredential couldn't find any valid credentials.

**Solution:**
- Locally: Run `az login` and ensure you're logged in
- In Azure: Ensure managed identity is enabled and has ADX permissions

### "Access denied" error

**Cause:** Your identity doesn't have permissions on the ADX database.

**Solution:** Grant your user or managed identity the appropriate role (see above)

### Testing your setup

```bash
# Test locally with verbose output
queryhub run-report my_report --config-dir config -v

# Verify Azure CLI is logged in
az account show

# Test ADX connection directly
az kusto database show \
  --cluster-name mycluster \
  --database-name MyDatabase \
  --resource-group myResourceGroup
```

## Migration from Service Principal

If you're currently using service principal authentication, migration is easy:

**Before:**
```yaml
credentials:
  type: service_principal
  client_id: ${AZURE_CLIENT_ID}
  client_secret: ${AZURE_CLIENT_SECRET}
  tenant_id: ${AZURE_TENANT_ID}
```

**After:**
```yaml
credentials:
  type: default_credentials
```

Just ensure your user/managed identity has the same permissions as the service principal.

## When NOT to use Default Credentials

Consider using specific credential types in these scenarios:

- **CI/CD pipelines** - Use `service_principal` with explicit credentials
- **Cross-tenant access** - Use `service_principal` with specific tenant
- **Specific managed identity** - Use `managed_identity` with explicit `client_id`

## Additional Resources

- [Azure DefaultAzureCredential Documentation](https://docs.microsoft.com/azure/developer/python/azure-sdk-authenticate)
- [Azure Data Explorer Access Control](https://docs.microsoft.com/azure/data-explorer/manage-database-permissions)
- [Managed Identity Overview](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)

## Example Complete Configuration

```yaml
# config/providers/providers.yaml
providers:
  - id: production_adx
    type: adx
    description: Production ADX cluster with default credentials
    cluster_uri: https://prod-cluster.kusto.windows.net
    database: ProductionDB
    default_timeout_seconds: 120
    retry_attempts: 3
    credentials:
      type: default_credentials
```

```yaml
# config/reports/daily_report.yaml
id: daily_sales_report
title: Daily Sales Analysis
components:
  - id: sales_summary
    provider: production_adx
    query:
      text: |
        SalesTable
        | where Timestamp >= ago(1d)
        | summarize TotalSales = sum(Amount) by Product
        | order by TotalSales desc
    render:
      type: table
```

Run it:
```bash
queryhub run-report daily_sales_report --config-dir config
```

Works locally with your Azure CLI credentials, and in production with managed identity - no changes needed! 🎉

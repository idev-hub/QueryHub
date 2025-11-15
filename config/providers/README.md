# QueryHub Providers Configuration

This directory contains provider and credential configurations. Providers can be split across multiple files for better organization.

## Multi-File Support

All YAML files in this directory are automatically merged. Files are processed in alphabetical order, so you can use numeric prefixes for explicit ordering:

```
providers/
  credentials.yaml         # Shared credentials
  01_databases.yaml       # Database providers
  02_azure.yaml           # Azure Data Explorer providers
  03_rest_apis.yaml       # REST API providers
  04_csv.yaml             # CSV file providers
```

## Credentials

Define reusable credentials that can be referenced by multiple providers:

```yaml
credentials:
  - id: azure_default_credentials
    azure:
      type: default_credentials
  
  - id: postgres_creds
    postgresql:
      type: username_password
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
```

## Providers

Define data source providers that reference credentials by ID:

```yaml
providers:
  - id: postgres_sales
    resource:
      sql:
        dsn: postgresql+asyncpg://localhost:5432/sales
    credentials: postgres_creds
  
  - id: adx_marketing
    resource:
      adx:
        cluster_uri: https://help.kusto.windows.net
        database: Samples
    credentials: azure_default_credentials
```

## Provider Types

Supported provider types:
- **SQL**: PostgreSQL, MySQL, SQL Server
- **ADX**: Azure Data Explorer (Kusto)
- **REST**: HTTP REST APIs
- **CSV**: Local CSV files
- **S3**: AWS S3 (future)
- **Athena**: AWS Athena (future)
- **BigQuery**: Google BigQuery (future)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - Multi-Cloud Architecture Refactoring 🚀

- **BREAKING**: Complete architectural refactoring to support multiple cloud providers
  - Credentials are now separate, reusable entities with unique IDs
  - Providers reference credentials by ID instead of embedding them
  - New YAML structure: credentials organized by cloud provider (`azure:`, `aws:`, `gcp:`, `postgresql:`)
  - Provider configuration nested under `resource:` key
  - See migration guide below for updating existing configurations

- **BREAKING**: New provider folder structure
  - Moved from flat structure to cloud-organized folders
  - `providers/azure/` - Azure implementations (ADX)
  - `providers/aws/` - AWS implementations (future: S3, Athena)
  - `providers/gcp/` - GCP implementations (future: BigQuery)
  - `providers/generic/` - Cloud-agnostic implementations (SQL, REST, CSV)
  - Each folder has `credentials.py` and `resources/` subfolder

- **BREAKING**: Updated import paths
  - `from queryhub.providers import BaseQueryProvider, QueryResult` (new)
  - `from queryhub.providers.base_credentials import BaseCredential` (new)
  - Old imports from `providers.base` and `providers.credentials` removed

### Added

- **Multi-Cloud Credential Support**
  - Azure: Default credentials, Managed Identity, Service Principal, Token
  - AWS: Default credentials, Access Key, IAM Role
  - GCP: Default credentials, Service Account
  - Generic: Username/Password, Token, Connection String, No credential

- **New Base Abstractions**
  - `BaseCredential[TConnection]` - Generic credential base with `get_connection()` method
  - `BaseQueryProvider` - Query provider base with `execute()` method
  - Type-safe implementations with generic type parameters

- **Credential Registry System**
  - `CredentialRegistry` - Manages credential lifecycle with caching
  - Lazy initialization - credentials created only when needed
  - Thread-safe credential instance management
  - Reusable credentials across multiple providers

- **Factory Pattern Implementation**
  - `credential_factory.py` - Routes credential creation by cloud provider
  - `provider_factory.py` - Routes provider creation by resource type
  - Dynamic module loading for lazy imports
  - Extensible design for adding new clouds/providers

- **Comprehensive Documentation**
  - `docs/reference/architecture.md` - Complete architecture guide
  - SOLID principles implementation throughout
  - Configuration examples for all cloud providers
  - Migration guide for existing users

- **Security Tools** (from previous release)
  - Bandit for security linting (detects common security issues)
  - Safety for dependency vulnerability scanning
  - Added configuration files: `.bandit` and `.safety-policy.yml`
  - Integrated both tools into CI/CD pipeline
  - Added `make security` and `make safety-check` targets
  - Added documentation in `docs/reference/security-tools.md`

### Changed (Previous)

- **BREAKING**: Migrated from pip to uv for dependency management
  - Updated all CI/CD workflows to use `astral-sh/setup-uv@v5`
  - Replaced `setuptools` with `hatchling` as build backend
  - Updated Makefile targets to use `uv sync` instead of `pip install`
  - Updated setup script and all documentation
  - See `docs/guides/uv-migration.md` for migration instructions

- Added `uv.lock` for deterministic dependency resolution
- Added `.python-version` file for Python version specification
- Added uv badge to README
- Added comprehensive uv migration guide
- Added "How to add a new provider" section to README with detailed examples

### Migration Guide - Credential Refactoring

#### Old Configuration Format (Deprecated ❌)
```yaml
providers:
  - id: adx_marketing
    type: adx
    cluster_uri: https://help.kusto.windows.net
    database: Samples
    credentials:
      type: managed_identity
      client_id: ${ADX_CLIENT_ID}
```

#### New Configuration Format (Required ✅)
```yaml
# Step 1: Define credentials with unique IDs
credentials:
  - id: azure_managed_identity
    azure:
      type: managed_identity
      client_id: ${ADX_CLIENT_ID}

# Step 2: Providers reference credentials by ID
providers:
  - id: adx_marketing
    resource:
      adx:
        cluster_uri: https://help.kusto.windows.net
        database: Samples
    credentials: azure_managed_identity
```

#### Key Benefits
- **Credential Reusability**: One credential shared across multiple providers
- **Better Security**: Credentials centralized in one section
- **Multi-Cloud Ready**: Native support for Azure, AWS, GCP
- **Type Safety**: Generic `BaseCredential[TConnection]` ensures correctness
- **Extensibility**: Add new clouds by creating a single strategy module

#### Code Changes Required
If you've extended QueryHub with custom providers:

```python
# Old approach ❌
from queryhub.providers.base import QueryProvider

class MyProvider(QueryProvider):
    async def execute(self, query: str):
        # Old credential access
        creds = self.config.credentials
```

```python
# New approach ✅
from queryhub.providers import BaseQueryProvider
from queryhub.core.credentials import CredentialRegistry

class MyProvider(BaseQueryProvider):
    def __init__(self, config, credential_registry: CredentialRegistry):
        super().__init__(config)
        self._credential_registry = credential_registry
    
    async def execute(self, query: str):
        # New credential access
        credential = await self._credential_registry.get_credential(
            self.config.credentials
        )
        connection = await credential.get_connection()
```

### Removed

- Deleted legacy credential system in `providers/credentials/` folder
- Removed old provider files: `adx.py`, `sql.py`, `rest.py`, `csv.py` from providers root
- Removed `build_default_provider_registry()` function (use `ProviderRegistry()` directly)
- Removed backward compatibility code for old configuration format

### Fixed
- Suppressed false positive security warnings in credential type enums

### Documentation
- Updated README with uv installation instructions
- Updated all documentation to use uv instead of pip
- Added migration guide for existing contributors
- Enhanced security tools documentation
- Improved provider extension documentation

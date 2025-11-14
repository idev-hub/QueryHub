"""QueryHub providers package.

This package contains all query providers and credential strategies
organized by cloud provider.

Structure:
- base_credentials.py: Base credential abstraction
- base_query_provider.py: Base provider abstraction
- credential_factory.py: Factory for creating credentials
- provider_factory.py: Factory for creating providers
- azure/: Azure-specific implementations
- aws/: AWS-specific implementations
- gcp/: GCP-specific implementations
- generic/: Cloud-agnostic implementations (SQL, REST, CSV)
"""

from .base_credentials import BaseCredential
from .base_query_provider import BaseQueryProvider, QueryResult
from .credential_factory import create_credential
from .provider_factory import create_provider

__all__ = [
    "BaseCredential",
    "BaseQueryProvider",
    "QueryResult",
    "create_credential",
    "create_provider",
]

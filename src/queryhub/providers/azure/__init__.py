"""Azure provider package."""

from .credentials import (
    AzureDefaultCredential,
    AzureManagedIdentityCredential,
    AzureServicePrincipalCredential,
    AzureTokenCredential,
)

__all__ = [
    "AzureDefaultCredential",
    "AzureManagedIdentityCredential",
    "AzureServicePrincipalCredential",
    "AzureTokenCredential",
]

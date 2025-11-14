"""GCP credential implementations.

This module contains all credential strategies for GCP services.
"""

from __future__ import annotations

import json
from typing import Any

from ...config.credential_models import GCPCredentialConfig
from ...core.errors import ProviderInitializationError
from ..base_credentials import BaseCredential


class GCPDefaultCredential(BaseCredential[GCPCredentialConfig | None, Any]):
    """GCP Application Default Credentials - automatic credential discovery.

    Tries multiple authentication methods in order:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable
    2. gcloud auth application-default login credentials
    3. Compute Engine metadata service
    4. App Engine metadata service
    5. Cloud Run metadata service

    Works with: BigQuery, Cloud Storage, Pub/Sub, all GCP services
    """

    def __init__(self, config: GCPCredentialConfig | None = None) -> None:
        super().__init__(config)
        self._credentials = None

    async def get_connection(self, **context: Any) -> Any:
        """Get GCP connection using Application Default Credentials."""
        service_type = context.get("service_type", "bigquery")

        if service_type == "bigquery":
            return await self._get_bigquery_client(**context)
        else:
            raise ProviderInitializationError(
                f"GCP DefaultCredential does not support service_type='{service_type}'"
            )

    async def _get_bigquery_client(self, **context: Any) -> Any:
        """Get BigQuery client with Application Default Credentials."""
        try:
            from google.auth import default
            from google.cloud import bigquery
        except ImportError as exc:
            raise ProviderInitializationError(
                "google-cloud-bigquery is required. Install with: pip install google-cloud-bigquery"
            ) from exc

        project_id = context.get("project_id")
        location = context.get("location", "US")

        # Get default credentials
        credentials, project = default()

        if not project_id:
            project_id = project

        if not project_id:
            raise ProviderInitializationError(
                "project_id is required for BigQuery and could not be determined"
            )

        self._credentials = credentials
        return bigquery.Client(project=project_id, credentials=credentials, location=location)

    async def close(self) -> None:
        # GCP clients don't need explicit cleanup
        pass


class GCPServiceAccountJSONCredential(BaseCredential[GCPCredentialConfig, Any]):
    """GCP service account JSON authentication.

    Uses a service account JSON key file or inline JSON for authentication.
    Best for CI/CD pipelines.

    Works with: BigQuery, Cloud Storage, Pub/Sub, all GCP services
    """

    def __init__(self, config: GCPCredentialConfig) -> None:
        super().__init__(config)
        self._credentials = None

    async def get_connection(self, **context: Any) -> Any:
        """Get GCP connection using service account JSON."""
        service_type = context.get("service_type", "bigquery")

        if service_type == "bigquery":
            return await self._get_bigquery_client(**context)
        else:
            raise ProviderInitializationError(
                f"GCP ServiceAccountJSON does not support service_type='{service_type}'"
            )

    def _load_service_account_info(self) -> dict[str, Any]:
        """Load service account info from JSON."""
        assert self.config is not None, "Config is required"
        if hasattr(self.config, "service_account_json") and self.config.service_account_json:
            # Inline JSON
            json_str = self.config.service_account_json.get_secret_value()
            return json.loads(json_str)  # type: ignore[no-any-return]
        elif (
            hasattr(self.config, "service_account_json_path")
            and self.config.service_account_json_path
        ):
            # JSON file path
            with open(self.config.service_account_json_path, "r") as f:
                return json.load(f)  # type: ignore[no-any-return]
        else:
            raise ProviderInitializationError(
                "Either service_account_json or service_account_json_path must be provided"
            )

    async def _get_bigquery_client(self, **context: Any) -> Any:
        """Get BigQuery client with service account JSON."""
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as exc:
            raise ProviderInitializationError(
                "google-cloud-bigquery is required. Install with: pip install google-cloud-bigquery"
            ) from exc

        service_account_info = self._load_service_account_info()

        project_id = (
            context.get("project_id")
            or getattr(self.config, "project_id", None)
            or service_account_info.get("project_id")
        )
        location = context.get("location", "US")

        if not project_id:
            raise ProviderInitializationError("project_id is required for BigQuery")

        self._credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )

        return bigquery.Client(project=project_id, credentials=self._credentials, location=location)

    async def close(self) -> None:
        # GCP clients don't need explicit cleanup
        pass

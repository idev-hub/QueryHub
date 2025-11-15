"""AWS credential implementations.

This module contains all credential strategies for AWS services.
"""

from __future__ import annotations

from typing import Any

from ...config.credential_models import AWSCredentialConfig
from ...core.errors import ProviderInitializationError
from ..base_credentials import BaseCredential


class AWSDefaultCredential(BaseCredential[AWSCredentialConfig | None, Any]):
    """AWS default credential chain - automatic credential discovery.

    Tries multiple authentication methods in order:
    1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    2. Shared credentials file (~/.aws/credentials)
    3. AWS config file (~/.aws/config)
    4. IAM role for EC2 instances
    5. IAM role for ECS tasks
    6. IAM role for Lambda functions

    Works with: S3, Athena, Redshift, DynamoDB, all AWS services
    """

    def __init__(self, config: AWSCredentialConfig | None = None) -> None:
        super().__init__(config)
        self._session: Any = None

    async def get_connection(self, **context: Any) -> Any:
        """Get AWS connection using default credential chain."""
        try:
            import boto3
        except ImportError as exc:
            raise ProviderInitializationError(
                "boto3 is required for AWS. Install with: pip install boto3"
            ) from exc

        service_name = context.get("service_name", "s3")
        region_name = context.get("region_name", "us-east-1")

        self._session = boto3.Session()
        assert self._session is not None
        return self._session.client(service_name, region_name=region_name)

    async def close(self) -> None:
        # boto3 clients don't need explicit cleanup
        pass



class AWSAccessKeyCredential(BaseCredential[AWSCredentialConfig, Any]):
    """AWS access key and secret key authentication.

    Uses explicit AWS credentials for authentication.
    Best for CI/CD pipelines.

    Works with: S3, Athena, Redshift, DynamoDB, all AWS services
    """

    def __init__(self, config: AWSCredentialConfig) -> None:
        super().__init__(config)
        self._session: Any = None

    async def get_connection(self, **context: Any) -> Any:
        """Get AWS connection using access key."""
        try:
            import boto3
        except ImportError as exc:
            raise ProviderInitializationError(
                "boto3 is required for AWS. Install with: pip install boto3"
            ) from exc

        service_name = context.get("service_name", "s3")
        region_name = context.get("region_name") or getattr(self.config, "region", "us-east-1")

        assert self.config is not None, "Config is required"
        assert self.config.access_key_id is not None, "access_key_id is required"
        assert self.config.secret_access_key is not None, "secret_access_key is required"

        session_token = None
        if hasattr(self.config, "session_token") and self.config.session_token:
            session_token = self.config.session_token.get_secret_value()

        self._session = boto3.Session(
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key.get_secret_value(),
            aws_session_token=session_token,
            region_name=region_name,
        )

        assert self._session is not None
        return self._session.client(service_name, region_name=region_name)

    async def close(self) -> None:
        # boto3 clients don't need explicit cleanup
        pass


class AWSIAMRoleCredential(BaseCredential[AWSCredentialConfig, Any]):
    """AWS IAM role assumption authentication.

    Assumes an IAM role to get temporary credentials.
    Useful for cross-account access.

    Works with: S3, Athena, Redshift, DynamoDB, all AWS services
    """

    def __init__(self, config: AWSCredentialConfig) -> None:
        super().__init__(config)
        self._session: Any = None

    async def get_connection(self, **context: Any) -> Any:
        """Get AWS connection by assuming IAM role."""
        try:
            import boto3
        except ImportError as exc:
            raise ProviderInitializationError(
                "boto3 is required for AWS. Install with: pip install boto3"
            ) from exc

        service_name = context.get("service_name", "s3")
        region_name = context.get("region_name") or getattr(self.config, "region", "us-east-1")

        assert self.config is not None, "Config is required"
        assert self.config.role_arn is not None, "role_arn is required"

        # Assume role to get temporary credentials
        sts_client = boto3.client("sts", region_name=region_name)
        assumed_role = sts_client.assume_role(
            RoleArn=self.config.role_arn,
            RoleSessionName=getattr(self.config, "role_session_name", "queryhub-session"),
        )

        credentials = assumed_role["Credentials"]

        # Create session with temporary credentials
        self._session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

        assert self._session is not None
        return self._session.client(service_name, region_name=region_name)

    async def close(self) -> None:
        # boto3 clients don't need explicit cleanup
        pass

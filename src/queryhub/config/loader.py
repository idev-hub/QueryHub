"""Utilities for loading QueryHub configuration from YAML files."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from pydantic import TypeAdapter

from ..core.credentials import CredentialRegistry
from ..core.errors import ConfigurationError
from .credential_models import CredentialConfig
from .environment import EnvironmentSubstitutor
from .models import ReportConfig, Settings, SMTPConfig
from .provider_models import ProviderConfig

_LOGGER = logging.getLogger(__name__)

_PROVIDER_ADAPTER: TypeAdapter[ProviderConfig] = TypeAdapter(ProviderConfig)
_REPORT_ADAPTER: TypeAdapter[ReportConfig] = TypeAdapter(ReportConfig)
_CREDENTIAL_ADAPTER: TypeAdapter[CredentialConfig] = TypeAdapter(CredentialConfig)


class YAMLFileReader:
    """Read and parse YAML files (SRP)."""

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    def read_file(self, path: Path) -> Any:
        """Read and parse a single YAML file."""
        if not path.exists():
            _LOGGER.debug("Config file %s not found", path)
            return None

        _LOGGER.debug("Reading configuration file: %s", path)
        with path.open("r", encoding=self._encoding) as handle:
            raw = handle.read()

        data = yaml.safe_load(raw)
        if data is None:
            _LOGGER.debug("Configuration file %s is empty", path)
            return None

        _LOGGER.debug("Successfully loaded configuration from: %s", path)
        return data

    def read_directory(self, directory: Path) -> list[Any]:
        """Read all YAML files from a directory."""
        documents: list[Any] = []
        if not directory.exists():
            _LOGGER.debug("Config directory %s not found", directory)
            return documents

        _LOGGER.debug("Reading configuration directory: %s", directory)
        yaml_files = sorted(directory.glob("*.y*ml"))
        _LOGGER.debug("Found %d YAML file(s) in %s", len(yaml_files), directory)
        
        for file_path in yaml_files:
            data = self.read_file(file_path)
            if data:
                documents.extend(self._extract_collection_items(data, file_path))

        _LOGGER.debug("Loaded %d document(s) from directory: %s", len(documents), directory)
        return documents

    def _extract_collection_items(self, data: Any, origin: Path) -> list[Any]:
        """Extract items from collection data."""
        if isinstance(data, Mapping):
            # Handle nested collections
            if "providers" in data:
                extracted = data.get("providers")
                return self._ensure_list(extracted, origin)
            if "reports" in data:
                extracted = data.get("reports")
                return self._ensure_list(extracted, origin)
            return [self._ensure_mapping(data, origin)]

        if isinstance(data, list):
            return self._ensure_list(data, origin)

        raise ConfigurationError(f"Unsupported YAML root type in {origin}: {type(data).__name__}")

    @staticmethod
    def _ensure_list(data: Any, origin: Path) -> list[dict[str, Any]]:
        """Ensure data is a list of mappings."""
        if isinstance(data, list):
            return [YAMLFileReader._ensure_mapping(item, origin) for item in data]
        if isinstance(data, Mapping):
            return [YAMLFileReader._ensure_mapping(data, origin)]
        raise ConfigurationError(
            f"Expected list or mapping in {origin}, found {type(data).__name__}"
        )

    @staticmethod
    def _ensure_mapping(data: Any, origin: Path) -> dict[str, Any]:
        """Ensure data is a mapping."""
        if isinstance(data, Mapping):
            return dict(data)
        raise ConfigurationError(f"Expected mapping in {origin}, found {type(data).__name__}")


class ConfigParser:
    """Parse and validate configuration data (SRP)."""

    @staticmethod
    def parse_providers(definitions: Iterable[Mapping[str, Any]]) -> dict[str, ProviderConfig]:
        """Parse provider definitions.

        Returns dict mapping provider ID to ProviderConfig.
        """
        _LOGGER.debug("Parsing provider definitions")
        registry: dict[str, ProviderConfig] = {}
        for item in definitions:
            provider = _PROVIDER_ADAPTER.validate_python(item)
            if provider.id in registry:
                raise ConfigurationError(f"Duplicate provider id '{provider.id}' detected")
            registry[provider.id] = provider
            _LOGGER.debug("Registered provider: %s (type=%s)", provider.id, provider.type)
        _LOGGER.info("Loaded %d provider(s)", len(registry))
        return registry

    @staticmethod
    def parse_reports(definitions: Iterable[Mapping[str, Any]]) -> dict[str, ReportConfig]:
        """Parse report definitions."""
        _LOGGER.debug("Parsing report definitions")
        registry: dict[str, ReportConfig] = {}
        for item in definitions:
            report = _REPORT_ADAPTER.validate_python(item)
            if report.id in registry:
                raise ConfigurationError(f"Duplicate report id '{report.id}' detected")
            registry[report.id] = report
            _LOGGER.debug(
                "Registered report: %s (title='%s', components=%d)",
                report.id,
                report.title,
                len(report.components),
            )
        _LOGGER.info("Loaded %d report(s)", len(registry))
        return registry

    @staticmethod
    def parse_credentials(definitions: Iterable[Mapping[str, Any]]) -> CredentialRegistry:
        """Parse credential definitions into a credential registry.

        Returns CredentialRegistry with all credentials registered.
        """
        _LOGGER.debug("Parsing credential definitions")
        registry = CredentialRegistry()
        credential_count = 0
        for item in definitions:
            credential = _CREDENTIAL_ADAPTER.validate_python(item)
            if not credential.id:
                raise ConfigurationError("Credential definitions must have an 'id' field")

            # Determine cloud provider and type from nested structure
            cloud_provider = credential.get_cloud_provider()
            credential_type = credential.get_credential_type()
            credential_config = credential.get_credential_config()

            registry.register(credential.id, cloud_provider, credential_type, credential_config)  # type: ignore[arg-type]
            _LOGGER.debug(
                "Registered credential: %s (provider=%s, type=%s)",
                credential.id,
                cloud_provider,
                credential_type,
            )
            credential_count += 1

        _LOGGER.info("Loaded %d credential(s)", credential_count)
        return registry


class ConfigLoader:
    """Load QueryHub settings from a configuration directory (Facade Pattern)."""

    def __init__(
        self,
        root_path: Path | str,
        *,
        environment: Mapping[str, str] | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._root = Path(root_path)
        self._substitutor = EnvironmentSubstitutor(environment)
        self._reader = YAMLFileReader(encoding)
        self._parser = ConfigParser()

    @property
    def root(self) -> Path:
        """Return the configuration root path."""
        return self._root

    async def load(self) -> Settings:
        """Load asynchronous settings wrapper."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.load_sync)

    def load_sync(self) -> Settings:
        """Synchronous loading entry point."""
        _LOGGER.info("Loading QueryHub configuration from: %s", self._root)
        
        _LOGGER.debug("Loading SMTP configuration")
        smtp_data = self._load_and_substitute_file(self._root / "smtp.yaml")
        
        _LOGGER.debug("Loading provider configurations")
        providers_data = self._load_and_substitute_collection(self._root / "providers")
        
        _LOGGER.debug("Loading report configurations")
        reports_data = self._load_and_substitute_collection(self._root / "reports")
        
        _LOGGER.debug("Loading credential configurations")
        credentials_data = self._load_and_substitute_collection(self._root / "credentials")

        smtp = SMTPConfig.model_validate(smtp_data or {})
        _LOGGER.debug("SMTP configuration loaded: host=%s, port=%d", smtp.host, smtp.port)
        
        providers = self._parser.parse_providers(providers_data)
        reports = self._parser.parse_reports(reports_data)
        credentials_registry = self._parser.parse_credentials(credentials_data)

        _LOGGER.info("Configuration loaded successfully")
        return Settings(
            smtp=smtp,
            providers=providers,
            reports=reports,
            credential_registry=credentials_registry,
        )

    def _load_and_substitute_file(self, path: Path) -> Any:
        """Load file and apply environment substitution."""
        data = self._reader.read_file(path)
        if data is None:
            return None
        return self._substitutor.substitute_in_data(data)

    def _load_and_substitute_collection(self, directory: Path) -> list[dict[str, Any]]:
        """Load collection and apply environment substitution."""
        documents = self._reader.read_directory(directory)
        return [self._substitutor.substitute_in_data(doc) for doc in documents]

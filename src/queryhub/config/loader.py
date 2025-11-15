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
from .models import (
    QueryComponentConfig,
    ReportConfig,
    ReportMetadataConfig,
    Settings,
    SMTPConfig,
)
from .provider_models import ProviderConfig

_LOGGER = logging.getLogger(__name__)

_PROVIDER_ADAPTER: TypeAdapter[ProviderConfig] = TypeAdapter(ProviderConfig)
_REPORT_ADAPTER: TypeAdapter[ReportConfig] = TypeAdapter(ReportConfig)
_REPORT_METADATA_ADAPTER: TypeAdapter[ReportMetadataConfig] = TypeAdapter(ReportMetadataConfig)
_COMPONENT_ADAPTER: TypeAdapter[QueryComponentConfig] = TypeAdapter(QueryComponentConfig)
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

    def read_directory(self, directory: Path, pattern: str = "*.y*ml") -> list[Any]:
        """Read all YAML files from a directory sorted by name."""
        documents: list[Any] = []
        if not directory.exists():
            _LOGGER.debug("Config directory %s not found", directory)
            return documents

        _LOGGER.debug("Reading configuration directory: %s", directory)
        yaml_files = sorted(directory.glob(pattern))
        _LOGGER.debug("Found %d YAML file(s) in %s", len(yaml_files), directory)
        
        for file_path in yaml_files:
            data = self.read_file(file_path)
            if data:
                documents.append(data)

        _LOGGER.debug("Loaded %d document(s) from directory: %s", len(documents), directory)
        return documents

    def read_providers_directory(self, directory: Path) -> list[Any]:
        """Read provider definitions from directory, supporting both single and multi-file formats."""
        documents: list[Any] = []
        if not directory.exists():
            _LOGGER.debug("Config directory %s not found", directory)
            return documents

        _LOGGER.debug("Reading provider configuration directory: %s", directory)
        yaml_files = sorted(directory.glob("*.y*ml"))
        _LOGGER.debug("Found %d YAML file(s) in %s", len(yaml_files), directory)
        
        for file_path in yaml_files:
            data = self.read_file(file_path)
            if data:
                documents.extend(self._extract_collection_items(data, file_path))

        _LOGGER.debug("Loaded %d provider(s) from directory: %s", len(documents), directory)
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
    def parse_report_folder(report_folder: Path) -> ReportConfig:
        """Parse a folder-based report configuration.
        
        Expected structure:
        - metadata.yaml: Report metadata (id, title, description, etc.)
        - Component files (numbered): 01_component.yaml, 02_component.yaml, etc.
        
        Auto-discovers templates and providers based on metadata or defaults.
        """
        _LOGGER.debug("Parsing report folder: %s", report_folder)
        
        if not report_folder.is_dir():
            raise ConfigurationError(f"Report path is not a directory: {report_folder}")
        
        # Read metadata
        metadata_path = report_folder / "metadata.yaml"
        if not metadata_path.exists():
            metadata_path = report_folder / "metadata.yml"
        
        if not metadata_path.exists():
            raise ConfigurationError(f"No metadata.yaml found in report folder: {report_folder}")
        
        reader = YAMLFileReader()
        metadata_data = reader.read_file(metadata_path)
        if not metadata_data:
            raise ConfigurationError(f"Empty metadata file: {metadata_path}")
        
        metadata = _REPORT_METADATA_ADAPTER.validate_python(metadata_data)
        _LOGGER.debug("Loaded metadata for report: %s", metadata.id)
        
        # Read component files (sorted by filename for numeric ordering)
        component_files = sorted(report_folder.glob("*.y*ml"))
        # Exclude metadata file
        component_files = [f for f in component_files if f.stem not in ("metadata",)]
        
        components: list[QueryComponentConfig] = []
        for component_file in component_files:
            _LOGGER.debug("Reading component file: %s", component_file)
            component_data = reader.read_file(component_file)
            if component_data:
                component = _COMPONENT_ADAPTER.validate_python(component_data)
                components.append(component)
                _LOGGER.debug("Loaded component: %s", component.id)
        
        if not components:
            _LOGGER.warning("No components found in report folder: %s", report_folder)
        
        # Determine template (just the filename, path resolution happens elsewhere)
        template = metadata.template or "report.html.j2"
        
        # Build ReportConfig
        report = ReportConfig(
            id=metadata.id,
            title=metadata.title,
            description=metadata.description,
            template=template,
            components=components,
            layout=metadata.layout,
            email=metadata.email,
            schedule=metadata.schedule,
            tags=metadata.tags,
        )
        
        _LOGGER.info(
            "Loaded report '%s' with %d components from folder: %s",
            report.id,
            len(components),
            report_folder,
        )
        return report

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
        # Try new location first (config/smtp/default.yaml), then old location (config/smtp.yaml)
        smtp_path = self._root / "smtp" / "default.yaml"
        if not smtp_path.exists():
            smtp_path = self._root / "smtp.yaml"
        
        smtp_data = None
        if smtp_path.exists():
            smtp_data = self._load_and_substitute_file(smtp_path)
        
        _LOGGER.debug("Loading provider configurations")
        providers_data = self._load_and_substitute_providers(self._root / "providers")
        
        _LOGGER.debug("Loading report configurations")
        reports = self._load_reports_from_folders(self._root / "reports")
        
        _LOGGER.debug("Loading credential configurations")
        credentials_data = self._load_and_substitute_collection(self._root / "credentials")

        # SMTP config is optional (for HTML-only mode)
        if smtp_data:
            smtp = SMTPConfig.model_validate(smtp_data)
            _LOGGER.debug("SMTP configuration loaded: host=%s, port=%d", smtp.host, smtp.port)
        else:
            smtp = SMTPConfig.model_validate({"host": "localhost"})  # Minimal valid config
            _LOGGER.debug("No SMTP configuration found, using minimal config (HTML-only mode)")
        
        providers = self._parser.parse_providers(providers_data)
        credentials_registry = self._parser.parse_credentials(credentials_data)

        _LOGGER.info("Configuration loaded successfully")
        return Settings(
            smtp=smtp,
            providers=providers,
            reports=reports,
            credential_registry=credentials_registry,
        )

    def load_report_from_folder(self, report_folder: Path | str) -> ReportConfig:
        """Load a single report from a folder path.
        
        This is the new primary method for loading reports.
        Auto-discovers templates and providers based on metadata configuration.
        """
        report_path = Path(report_folder)
        _LOGGER.info("Loading report from folder: %s", report_path)
        
        # Load metadata
        metadata_path = report_path / "metadata.yaml"
        if not metadata_path.exists():
            metadata_path = report_path / "metadata.yml"
        
        if not metadata_path.exists():
            raise ConfigurationError(f"No metadata.yaml found in report folder: {report_path}")
        
        metadata_data = self._reader.read_file(metadata_path)
        if not metadata_data:
            raise ConfigurationError(f"Empty metadata file: {metadata_path}")
        
        # Parse the report using the report folder
        report = self._parser.parse_report_folder(report_path)
        return report
    
    @staticmethod
    def resolve_template_folder(report_folder: Path, metadata_template_folder: str | None = None) -> Path:
        """Resolve the template folder path.
        
        Priority:
        1. metadata.template_folder (if specified)
        2. report_folder/../../templates (default: config/templates)
        """
        if metadata_template_folder:
            template_path = Path(metadata_template_folder)
            if not template_path.is_absolute():
                template_path = report_folder / template_path
            if template_path.exists():
                return template_path.resolve()
        
        # Default: config/templates (go up from report to config root)
        default_templates = report_folder.parent.parent / "templates"
        if default_templates.exists():
            return default_templates.resolve()
        
        # Fallback to old templates location
        fallback_templates = Path("templates")
        if fallback_templates.exists():
            return fallback_templates.resolve()
        
        raise ConfigurationError(
            f"Template folder not found. Tried: {default_templates}, {fallback_templates}"
        )
    
    @staticmethod
    def resolve_providers_folder(report_folder: Path, metadata_providers_folder: str | None = None) -> Path:
        """Resolve the providers folder path.
        
        Priority:
        1. metadata.providers_folder (if specified)
        2. report_folder/../../providers (default: config/providers)
        """
        if metadata_providers_folder:
            providers_path = Path(metadata_providers_folder)
            if not providers_path.is_absolute():
                providers_path = report_folder / metadata_providers_folder
            if providers_path.exists():
                return providers_path.resolve()
        
        # Default: config/providers (go up from report to config root)
        default_providers = report_folder.parent.parent / "providers"
        if default_providers.exists():
            return default_providers.resolve()
        
        raise ConfigurationError(
            f"Providers folder not found. Tried: {default_providers}"
        )
    
    @staticmethod
    def resolve_smtp_config_path(report_folder: Path, metadata_smtp_config: str | None = None) -> Path | None:
        """Resolve the SMTP config file path.
        
        Priority:
        1. metadata.smtp_config (if specified) - looks in config/smtp/
        2. report_folder/../../smtp/default.yaml (default: config/smtp/default.yaml)
        
        Returns None if no SMTP config is found (HTML-only mode).
        """
        config_root = report_folder.parent.parent  # config/reports/report_name -> config
        smtp_folder = config_root / "smtp"
        
        if metadata_smtp_config:
            # Look for specified SMTP config in smtp folder
            smtp_file = smtp_folder / metadata_smtp_config
            if not smtp_file.suffix:
                smtp_file = smtp_folder / f"{metadata_smtp_config}.yaml"
            if smtp_file.exists():
                return smtp_file.resolve()
            raise ConfigurationError(
                f"SMTP config '{metadata_smtp_config}' not found in {smtp_folder}"
            )
        
        # Default: config/smtp/default.yaml
        default_smtp = smtp_folder / "default.yaml"
        if default_smtp.exists():
            return default_smtp.resolve()
        
        # No SMTP config found - HTML-only mode
        return None

    def _load_reports_from_folders(self, reports_dir: Path) -> dict[str, ReportConfig]:
        """Load all reports from subdirectories in the reports folder."""
        registry: dict[str, ReportConfig] = {}
        
        if not reports_dir.exists():
            _LOGGER.debug("Reports directory not found: %s", reports_dir)
            return registry
        
        _LOGGER.debug("Scanning reports directory: %s", reports_dir)
        
        # Each subdirectory is a report
        for report_folder in sorted(reports_dir.iterdir()):
            if not report_folder.is_dir():
                continue
            
            try:
                report = self._parser.parse_report_folder(report_folder)
                if report.id in registry:
                    raise ConfigurationError(f"Duplicate report id '{report.id}' detected")
                registry[report.id] = report
            except Exception as exc:
                _LOGGER.error("Failed to load report from %s: %s", report_folder, exc)
                raise
        
        _LOGGER.info("Loaded %d report(s) from folders", len(registry))
        return registry

    def _load_and_substitute_file(self, path: Path) -> Any:
        """Load file and apply environment substitution."""
        data = self._reader.read_file(path)
        if data is None:
            return None
        return self._substitutor.substitute_in_data(data)

    def _load_and_substitute_providers(self, directory: Path) -> list[dict[str, Any]]:
        """Load providers supporting multi-file format."""
        documents = self._reader.read_providers_directory(directory)
        return [self._substitutor.substitute_in_data(doc) for doc in documents]

    def _load_and_substitute_collection(self, directory: Path) -> list[dict[str, Any]]:
        """Load collection and apply environment substitution."""
        documents = self._reader.read_directory(directory)
        return [self._substitutor.substitute_in_data(doc) for doc in documents]

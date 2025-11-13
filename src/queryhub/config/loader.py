"""Utilities for loading QueryHub configuration from YAML files."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping

import yaml

from pydantic import TypeAdapter

from .models import ProviderConfig, ReportConfig, Settings, SMTPConfig

_LOGGER = logging.getLogger(__name__)
_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(?::([^}]+))?}")

_PROVIDER_ADAPTER = TypeAdapter(ProviderConfig)
_REPORT_ADAPTER = TypeAdapter(ReportConfig)


class ConfigLoader:
    """Load QueryHub settings from a configuration directory."""

    def __init__(
        self,
        root_path: Path | str,
        *,
        environment: Mapping[str, str] | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._root = Path(root_path)
        self._environment = dict(environment or os.environ)
        self._encoding = encoding

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

        smtp_data = self._load_yaml_file(self._root / "smtp.yaml")
        providers_data = self._load_collection(self._root / "providers")
        reports_data = self._load_collection(self._root / "reports")

        smtp = SMTPConfig.model_validate(smtp_data or {})
        providers = self._parse_providers(providers_data)
        reports = self._parse_reports(reports_data)

        return Settings(smtp=smtp, providers=providers, reports=reports)

    def _load_collection(self, directory: Path) -> list[dict[str, Any]]:
        """Aggregate YAML documents from a directory."""

        documents: list[dict[str, Any]] = []
        if not directory.exists():
            _LOGGER.debug("Config directory %s not found", directory)
            return documents

        for file_path in sorted(directory.glob("*.y*ml")):
            data = self._load_yaml_file(file_path)
            if not data:
                continue
            if isinstance(data, Mapping):
                if "providers" in data:
                    extracted = data.get("providers")
                    documents.extend(self._ensure_list(extracted, file_path))
                elif "reports" in data:
                    extracted = data.get("reports")
                    documents.extend(self._ensure_list(extracted, file_path))
                else:
                    documents.append(self._ensure_mapping(data, file_path))
            elif isinstance(data, list):
                documents.extend(self._ensure_list(data, file_path))
            else:
                raise ValueError(f"Unsupported YAML root type in {file_path}: {type(data)!r}")
        return documents

    def _parse_providers(self, definitions: Iterable[Mapping[str, Any]]) -> dict[str, ProviderConfig]:
        registry: dict[str, ProviderConfig] = {}
        for item in definitions:
            data = self._resolve_environment(item)
            provider = _PROVIDER_ADAPTER.validate_python(data)
            if provider.id in registry:
                raise ValueError(f"Duplicate provider id '{provider.id}' detected")
            registry[provider.id] = provider
        return registry

    def _parse_reports(self, definitions: Iterable[Mapping[str, Any]]) -> dict[str, ReportConfig]:
        registry: dict[str, ReportConfig] = {}
        for item in definitions:
            data = self._resolve_environment(item)
            report = _REPORT_ADAPTER.validate_python(data)
            if report.id in registry:
                raise ValueError(f"Duplicate report id '{report.id}' detected")
            registry[report.id] = report
        return registry

    def _load_yaml_file(self, path: Path) -> Any:
        if not path.exists():
            _LOGGER.debug("Config file %s not found", path)
            return None
        with path.open("r", encoding=self._encoding) as handle:
            raw = handle.read()
        substituted = self._substitute_environment(raw)
        data = yaml.safe_load(substituted)
        if data is None:
            return None
        if isinstance(data, MutableMapping):
            return dict(data)
        if isinstance(data, list):
            return list(data)
        return data

    def _substitute_environment(self, payload: str) -> str:
        """Replace ${VAR[:default]} placeholders in raw YAML text."""

        def _replace(match: re.Match[str]) -> str:
            name, default = match.groups()
            if name in self._environment:
                return self._environment[name]
            if default is not None:
                return default
            raise KeyError(f"Environment variable '{name}' not found for configuration placeholder")

        return _ENV_PATTERN.sub(_replace, payload)

    def _resolve_environment(self, data: Any) -> Any:
        if isinstance(data, str):
            return self._substitute_environment(data) if "${" in data else data
        if isinstance(data, list):
            return [self._resolve_environment(item) for item in data]
        if isinstance(data, MutableMapping):
            return {key: self._resolve_environment(value) for key, value in data.items()}
        return data

    @staticmethod
    def _ensure_list(data: Any, origin: Path) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [ConfigLoader._ensure_mapping(item, origin) for item in data]
        if isinstance(data, Mapping):
            return [ConfigLoader._ensure_mapping(data, origin)]
        raise TypeError(f"Expected list or mapping in {origin}, found {type(data)!r}")

    @staticmethod
    def _ensure_mapping(data: Any, origin: Path) -> dict[str, Any]:
        if isinstance(data, Mapping):
            return dict(data)
        raise TypeError(f"Expected mapping in {origin}, found {type(data)!r}")

"""Environment variable substitution service (SRP)."""

from __future__ import annotations

import os
import re
from typing import Any, Mapping, MutableMapping

from ..core.errors import ConfigurationError

_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(?::([^}]+))?}")


class EnvironmentSubstitutor:
    """Handle environment variable substitution in configuration (Strategy Pattern)."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = dict(environment or os.environ)

    def substitute_in_text(self, text: str) -> str:
        """Replace ${VAR[:default]} placeholders in text."""
        if "${" not in text:
            return text

        def _replace(match: re.Match[str]) -> str:
            name, default = match.groups()
            if name in self._environment:
                return self._environment[name]
            if default is not None:
                return default
            raise ConfigurationError(
                f"Environment variable '{name}' not found for configuration placeholder"
            )

        return _ENV_PATTERN.sub(_replace, text)

    def substitute_in_data(self, data: Any) -> Any:
        """Recursively substitute environment variables in data structures."""
        if isinstance(data, str):
            return self.substitute_in_text(data)
        if isinstance(data, list):
            return [self.substitute_in_data(item) for item in data]
        if isinstance(data, MutableMapping):
            return {key: self.substitute_in_data(value) for key, value in data.items()}
        return data

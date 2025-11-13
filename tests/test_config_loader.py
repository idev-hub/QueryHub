"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

from queryhub.config import ConfigLoader
from queryhub.config.models import ProviderType


def test_load_settings_with_environment(monkeypatch) -> None:
    fixtures_dir = Path("tests/fixtures/config_basic")
    csv_root = Path("tests/fixtures/data").resolve()
    monkeypatch.setenv("CSV_ROOT", str(csv_root))

    loader = ConfigLoader(fixtures_dir)
    settings = loader.load_sync()

    assert "csv_fixture" in settings.providers
    provider = settings.providers["csv_fixture"]
    assert provider.type is ProviderType.CSV
    assert settings.smtp.default_from == "reports@example.test"

"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path


from queryhub.config import ConfigLoader


def test_load_settings_with_environment(monkeypatch) -> None:
    fixtures_dir = Path("tests/fixtures/config_basic")
    csv_root = Path("tests/fixtures/data").resolve()
    monkeypatch.setenv("CSV_ROOT", str(csv_root))

    loader = ConfigLoader(fixtures_dir)
    settings = loader.load_sync()

    assert "csv_fixture" in settings.providers
    provider = settings.providers["csv_fixture"]
    assert provider.type == "csv"  # String comparison instead of enum
    assert settings.smtp.default_from == "reports@example.test"


def test_load_settings_with_credentials_in_providers_dir(tmp_path: Path, monkeypatch) -> None:
    """Test loading configuration with credentials in providers directory."""
    # Create config structure
    providers_dir = tmp_path / "providers"
    smtp_dir = tmp_path / "smtp"
    providers_dir.mkdir()
    smtp_dir.mkdir()

    # Create providers file with both credentials and providers
    providers_yaml = """
credentials:
  - id: test_cred
    postgresql:
      type: username_password
      username: testuser
      password: testpass

providers:
  - id: test_provider
    resource:
      sql:
        dsn: postgresql://localhost/testdb
    credentials: test_cred
"""
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    # Create minimal SMTP config
    smtp_yaml = """
host: localhost
port: 1025
use_tls: false
default_from: test@example.com
"""
    (smtp_dir / "default.yaml").write_text(smtp_yaml, encoding="utf-8")

    # Load configuration
    loader = ConfigLoader(tmp_path)
    settings = loader.load_sync()

    # Verify provider loaded
    assert "test_provider" in settings.providers
    assert settings.providers["test_provider"].type == "sql"
    assert settings.providers["test_provider"].credentials == "test_cred"

    # Verify credential loaded
    assert "test_cred" in settings.credential_registry
    assert len(settings.credential_registry) == 1


def test_load_settings_with_credentials_split_across_files(tmp_path: Path, monkeypatch) -> None:
    """Test loading configuration with credentials split across multiple files."""
    providers_dir = tmp_path / "providers"
    smtp_dir = tmp_path / "smtp"
    providers_dir.mkdir()
    smtp_dir.mkdir()

    # File 1: Credentials only
    credentials_yaml = """
credentials:
  - id: postgres_cred
    postgresql:
      type: username_password
      username: pguser
      password: pgpass
  
  - id: api_token
    generic:
      type: token
      token: secret123
"""
    (providers_dir / "01_credentials.yaml").write_text(credentials_yaml, encoding="utf-8")

    # File 2: Database providers
    db_providers_yaml = """
providers:
  - id: postgres_db
    resource:
      sql:
        dsn: postgresql://localhost/db1
    credentials: postgres_cred
"""
    (providers_dir / "02_databases.yaml").write_text(db_providers_yaml, encoding="utf-8")

    # File 3: API providers
    api_providers_yaml = """
providers:
  - id: rest_api
    resource:
      rest:
        base_url: https://api.example.com
    credentials: api_token
"""
    (providers_dir / "03_apis.yaml").write_text(api_providers_yaml, encoding="utf-8")

    # SMTP config
    (smtp_dir / "default.yaml").write_text("host: localhost\nport: 1025\nuse_tls: false\ndefault_from: test@example.com", encoding="utf-8")

    # Load configuration
    loader = ConfigLoader(tmp_path)
    settings = loader.load_sync()

    # Verify all providers loaded
    assert len(settings.providers) == 2
    assert "postgres_db" in settings.providers
    assert "rest_api" in settings.providers

    # Verify all credentials loaded
    assert len(settings.credential_registry) == 2
    assert "postgres_cred" in settings.credential_registry
    assert "api_token" in settings.credential_registry


def test_load_settings_with_default_env_vars(tmp_path: Path, monkeypatch) -> None:
    """Test loading configuration with environment variable defaults."""
    providers_dir = tmp_path / "providers"
    smtp_dir = tmp_path / "smtp"
    providers_dir.mkdir()
    smtp_dir.mkdir()

    # Provider with env vars with defaults
    providers_yaml = """
providers:
  - id: test_provider
    resource:
      sql:
        dsn: postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/testdb
"""
    (providers_dir / "providers.yaml").write_text(providers_yaml, encoding="utf-8")

    # SMTP config
    (smtp_dir / "default.yaml").write_text("host: localhost\nport: 1025\nuse_tls: false\ndefault_from: test@example.com", encoding="utf-8")

    # Don't set env vars - should use defaults
    loader = ConfigLoader(tmp_path)
    settings = loader.load_sync()

    assert "test_provider" in settings.providers
    # The DSN should have defaults substituted
    provider = settings.providers["test_provider"]
    dsn = provider.resource.sql.dsn
    assert "localhost" in dsn
    assert "5432" in dsn


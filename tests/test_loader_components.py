"""Tests for config loader components."""

from __future__ import annotations

from pathlib import Path

import pytest

from queryhub.config.loader import ConfigParser, YAMLFileReader
from queryhub.core.errors import ConfigurationError


def test_yaml_file_reader_read_file(tmp_path: Path) -> None:
    """Test reading a single YAML file."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("key: value\nnumber: 42", encoding="utf-8")

    reader = YAMLFileReader()
    data = reader.read_file(yaml_file)

    assert data == {"key": "value", "number": 42}


def test_yaml_file_reader_read_file_not_found(tmp_path: Path) -> None:
    """Test reading non-existent file returns None."""
    reader = YAMLFileReader()
    data = reader.read_file(tmp_path / "missing.yaml")

    assert data is None


def test_yaml_file_reader_read_file_empty(tmp_path: Path) -> None:
    """Test reading empty YAML file returns None."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("", encoding="utf-8")

    reader = YAMLFileReader()
    data = reader.read_file(yaml_file)

    assert data is None


def test_yaml_file_reader_read_directory(tmp_path: Path) -> None:
    """Test reading all YAML files from directory."""
    dir_path = tmp_path / "configs"
    dir_path.mkdir()

    (dir_path / "config1.yaml").write_text("id: first\ntype: test", encoding="utf-8")
    (dir_path / "config2.yml").write_text("id: second\ntype: test", encoding="utf-8")

    reader = YAMLFileReader()
    documents = reader.read_directory(dir_path)

    assert len(documents) == 2
    ids = [doc["id"] for doc in documents]
    assert "first" in ids
    assert "second" in ids


def test_yaml_file_reader_read_directory_not_found(tmp_path: Path) -> None:
    """Test reading non-existent directory returns empty list."""
    reader = YAMLFileReader()
    documents = reader.read_directory(tmp_path / "missing")

    assert documents == []


def test_yaml_file_reader_read_directory_with_providers_key(tmp_path: Path) -> None:
    """Test reading directory with providers key extracts items."""
    dir_path = tmp_path / "providers"
    dir_path.mkdir()

    yaml_content = """
providers:
  - id: provider1
    type: sql
  - id: provider2
    type: rest
"""
    (dir_path / "providers.yaml").write_text(yaml_content, encoding="utf-8")

    reader = YAMLFileReader()
    documents = reader.read_providers_directory(dir_path)

    assert len(documents) == 2
    assert documents[0]["id"] == "provider1"
    assert documents[1]["id"] == "provider2"


def test_yaml_file_reader_read_directory_with_reports_key(tmp_path: Path) -> None:
    """Test reading directory with reports key extracts items."""
    dir_path = tmp_path / "reports"
    dir_path.mkdir()

    yaml_content = """
reports:
  - id: report1
    title: First Report
  - id: report2
    title: Second Report
"""
    (dir_path / "reports.yaml").write_text(yaml_content, encoding="utf-8")

    reader = YAMLFileReader()
    # For reports, we now use folder-based loading, but test the old extraction logic
    documents = reader.read_providers_directory(dir_path)  # Uses same extraction logic

    assert len(documents) == 2
    assert documents[0]["id"] == "report1"
    assert documents[1]["id"] == "report2"


def test_yaml_file_reader_extract_collection_invalid_type(tmp_path: Path) -> None:
    """Test that invalid YAML root type raises error."""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("123", encoding="utf-8")  # Just a number

    reader = YAMLFileReader()
    data = reader.read_file(yaml_file)

    with pytest.raises(ConfigurationError, match="Unsupported YAML root type"):
        reader._extract_collection_items(data, yaml_file)


def test_config_parser_parse_providers() -> None:
    """Test parsing provider definitions."""
    definitions = [
        {
            "id": "test_sql",
            "type": "sql",
            "resource": {"sql": {"dsn": "sqlite:///:memory:"}},
        },
        {
            "id": "test_rest",
            "type": "rest",
            "resource": {"rest": {"base_url": "http://api.example.com"}},
        },
    ]

    providers = ConfigParser.parse_providers(definitions)

    assert len(providers) == 2
    assert "test_sql" in providers
    assert "test_rest" in providers
    assert providers["test_sql"].type == "sql"
    assert providers["test_rest"].type == "rest"


def test_config_parser_parse_providers_duplicate_id() -> None:
    """Test that duplicate provider IDs raise error."""
    definitions = [
        {
            "id": "duplicate",
            "type": "sql",
            "resource": {"sql": {"dsn": "sqlite:///:memory:"}},
        },
        {
            "id": "duplicate",
            "type": "rest",
            "resource": {"rest": {"base_url": "http://api.example.com"}},
        },
    ]

    with pytest.raises(ConfigurationError, match="Duplicate provider id 'duplicate'"):
        ConfigParser.parse_providers(definitions)


def test_config_parser_parse_reports() -> None:
    """Test parsing report definitions."""
    definitions = [
        {
            "id": "report1",
            "title": "First Report",
            "components": [
                {
                    "id": "comp1",
                    "provider": "test_provider",
                    "query": {},
                    "render": {"type": "table"},
                }
            ],
        },
        {
            "id": "report2",
            "title": "Second Report",
            "components": [
                {
                    "id": "comp2",
                    "provider": "test_provider",
                    "query": {},
                    "render": {"type": "chart"},
                }
            ],
        },
    ]

    reports = ConfigParser.parse_reports(definitions)

    assert len(reports) == 2
    assert "report1" in reports
    assert "report2" in reports
    assert reports["report1"].title == "First Report"
    assert reports["report2"].title == "Second Report"


def test_config_parser_parse_reports_duplicate_id() -> None:
    """Test that duplicate report IDs raise error."""
    definitions = [
        {
            "id": "duplicate",
            "title": "Report One",
            "components": [
                {
                    "id": "comp1",
                    "provider": "test_provider",
                    "query": {},
                    "render": {"type": "table"},
                }
            ],
        },
        {
            "id": "duplicate",
            "title": "Report Two",
            "components": [
                {
                    "id": "comp2",
                    "provider": "test_provider",
                    "query": {},
                    "render": {"type": "chart"},
                }
            ],
        },
    ]

    with pytest.raises(ConfigurationError, match="Duplicate report id 'duplicate'"):
        ConfigParser.parse_reports(definitions)


def test_config_parser_parse_credentials() -> None:
    """Test parsing credential definitions."""
    definitions = [
        {
            "id": "test_cred",
            "generic": {
                "type": "none",
            },
        },
    ]

    registry = ConfigParser.parse_credentials(definitions)

    assert len(registry) == 1
    assert "test_cred" in registry


def test_config_parser_parse_credentials_missing_id() -> None:
    """Test that credentials without ID raise error."""
    definitions = [
        {
            "generic": {
                "type": "none",
            },
        },
    ]

    with pytest.raises(Exception):  # Will raise validation error from Pydantic
        ConfigParser.parse_credentials(definitions)


def test_yaml_file_reader_sorts_files(tmp_path: Path) -> None:
    """Test that YAML files are read in sorted order."""
    dir_path = tmp_path / "configs"
    dir_path.mkdir()

    # Create files in non-alphabetical order
    (dir_path / "c.yaml").write_text("id: third", encoding="utf-8")
    (dir_path / "a.yaml").write_text("id: first", encoding="utf-8")
    (dir_path / "b.yaml").write_text("id: second", encoding="utf-8")

    reader = YAMLFileReader()
    documents = reader.read_directory(dir_path)

    # Should be sorted alphabetically by filename
    assert [doc["id"] for doc in documents] == ["first", "second", "third"]


def test_yaml_file_reader_custom_encoding(tmp_path: Path) -> None:
    """Test reading YAML with custom encoding."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("key: value", encoding="utf-16")

    reader = YAMLFileReader(encoding="utf-16")
    data = reader.read_file(yaml_file)

    assert data == {"key": "value"}


def test_yaml_file_reader_ensure_mapping_error(tmp_path: Path) -> None:
    """Test that non-mapping data raises error when mapping expected."""
    with pytest.raises(ConfigurationError, match="Expected mapping"):
        YAMLFileReader._ensure_mapping("not a mapping", tmp_path / "test.yaml")


def test_yaml_file_reader_ensure_list_with_dict() -> None:
    """Test ensure_list accepts a single dict and wraps it in a list."""
    result = YAMLFileReader._ensure_list({"id": "test"}, Path("test.yaml"))
    assert result == [{"id": "test"}]


def test_yaml_file_reader_ensure_list_with_list() -> None:
    """Test ensure_list accepts a list of dicts."""
    data = [{"id": "first"}, {"id": "second"}]
    result = YAMLFileReader._ensure_list(data, Path("test.yaml"))
    assert result == data


def test_yaml_file_reader_ensure_list_error() -> None:
    """Test ensure_list raises error for invalid data."""
    with pytest.raises(ConfigurationError, match="Expected list or mapping"):
        YAMLFileReader._ensure_list(123, Path("test.yaml"))


def test_yaml_file_reader_read_providers_directory_with_credentials(tmp_path: Path) -> None:
    """Test that credentials sections are skipped when reading providers."""
    dir_path = tmp_path / "providers"
    dir_path.mkdir()

    yaml_content = """
credentials:
  - id: test_cred
    generic:
      type: none

providers:
  - id: provider1
    resource:
      sql:
        dsn: "sqlite:///:memory:"
    credentials: test_cred
"""
    (dir_path / "providers.yaml").write_text(yaml_content, encoding="utf-8")

    reader = YAMLFileReader()
    documents = reader.read_providers_directory(dir_path)

    # Should only extract providers, not credentials
    assert len(documents) == 1
    assert documents[0]["id"] == "provider1"


def test_yaml_file_reader_read_credentials_from_providers_directory(tmp_path: Path) -> None:
    """Test extracting credentials from providers directory."""
    dir_path = tmp_path / "providers"
    dir_path.mkdir()

    yaml_content = """
credentials:
  - id: cred1
    generic:
      type: none
  - id: cred2
    postgresql:
      type: username_password
      username: user
      password: pass

providers:
  - id: provider1
    resource:
      sql:
        dsn: "sqlite:///:memory:"
"""
    (dir_path / "providers.yaml").write_text(yaml_content, encoding="utf-8")

    reader = YAMLFileReader()
    credentials = reader.read_credentials_from_providers_directory(dir_path)

    # Should extract both credentials
    assert len(credentials) == 2
    assert credentials[0]["id"] == "cred1"
    assert credentials[1]["id"] == "cred2"


def test_yaml_file_reader_read_credentials_from_multiple_files(tmp_path: Path) -> None:
    """Test extracting credentials from multiple files in providers directory."""
    dir_path = tmp_path / "providers"
    dir_path.mkdir()

    # File 1: credentials only
    (dir_path / "01_credentials.yaml").write_text("""
credentials:
  - id: cred1
    generic:
      type: none
""", encoding="utf-8")

    # File 2: both credentials and providers
    (dir_path / "02_providers.yaml").write_text("""
credentials:
  - id: cred2
    postgresql:
      type: username_password
      username: user
      password: pass

providers:
  - id: provider1
    resource:
      sql:
        dsn: "sqlite:///:memory:"
""", encoding="utf-8")

    # File 3: providers only (no credentials)
    (dir_path / "03_more_providers.yaml").write_text("""
providers:
  - id: provider2
    resource:
      csv:
        root_path: /data
""", encoding="utf-8")

    reader = YAMLFileReader()
    credentials = reader.read_credentials_from_providers_directory(dir_path)

    # Should extract credentials from files 1 and 2
    assert len(credentials) == 2
    credential_ids = [c["id"] for c in credentials]
    assert "cred1" in credential_ids
    assert "cred2" in credential_ids


def test_yaml_file_reader_read_credentials_no_credentials_section(tmp_path: Path) -> None:
    """Test that files without credentials section are handled gracefully."""
    dir_path = tmp_path / "providers"
    dir_path.mkdir()

    yaml_content = """
providers:
  - id: provider1
    resource:
      sql:
        dsn: "sqlite:///:memory:"
"""
    (dir_path / "providers.yaml").write_text(yaml_content, encoding="utf-8")

    reader = YAMLFileReader()
    credentials = reader.read_credentials_from_providers_directory(dir_path)

    # Should return empty list when no credentials found
    assert len(credentials) == 0


def test_yaml_file_reader_read_credentials_empty_directory(tmp_path: Path) -> None:
    """Test reading credentials from non-existent directory."""
    reader = YAMLFileReader()
    credentials = reader.read_credentials_from_providers_directory(tmp_path / "missing")

    assert credentials == []


def test_extract_collection_items_credentials_skipped(tmp_path: Path) -> None:
    """Test that _extract_collection_items skips credentials sections."""
    data = {
        "credentials": [
            {"id": "cred1", "generic": {"type": "none"}},
        ]
    }

    reader = YAMLFileReader()
    result = reader._extract_collection_items(data, tmp_path / "test.yaml")

    # Should return empty list, not the credentials
    assert result == []


def test_extract_collection_items_mixed_content(tmp_path: Path) -> None:
    """Test extraction with both providers and credentials in same file."""
    data = {
        "credentials": [
            {"id": "cred1", "generic": {"type": "none"}},
        ],
        "providers": [
            {"id": "provider1", "resource": {"sql": {"dsn": "sqlite:///:memory:"}}},
        ],
    }

    reader = YAMLFileReader()
    result = reader._extract_collection_items(data, tmp_path / "test.yaml")

    # Should only extract providers
    assert len(result) == 1
    assert result[0]["id"] == "provider1"

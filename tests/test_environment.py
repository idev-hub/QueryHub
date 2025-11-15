"""Tests for environment variable substitution."""

from __future__ import annotations

import pytest

from queryhub.config.environment import EnvironmentSubstitutor
from queryhub.core.errors import ConfigurationError


def test_substitute_no_placeholders() -> None:
    """Test substitution with no placeholders."""
    sub = EnvironmentSubstitutor({"KEY": "value"})
    result = sub.substitute_in_text("plain text")
    assert result == "plain text"


def test_substitute_single_variable() -> None:
    """Test substitution with single variable."""
    sub = EnvironmentSubstitutor({"VAR": "replacement"})
    result = sub.substitute_in_text("Hello ${VAR}")
    assert result == "Hello replacement"


def test_substitute_multiple_variables() -> None:
    """Test substitution with multiple variables."""
    sub = EnvironmentSubstitutor({"FIRST": "one", "SECOND": "two"})
    result = sub.substitute_in_text("${FIRST} and ${SECOND}")
    assert result == "one and two"


def test_substitute_with_default() -> None:
    """Test substitution with default value."""
    sub = EnvironmentSubstitutor({})
    result = sub.substitute_in_text("${MISSING:default_value}")
    assert result == "default_value"


def test_substitute_with_default_not_used() -> None:
    """Test that default is not used when variable exists."""
    sub = EnvironmentSubstitutor({"EXISTS": "actual"})
    result = sub.substitute_in_text("${EXISTS:default}")
    assert result == "actual"


def test_substitute_missing_variable_no_default() -> None:
    """Test substitution fails when variable is missing and no default."""
    sub = EnvironmentSubstitutor({})
    with pytest.raises(ConfigurationError, match="Environment variable 'MISSING' not found"):
        sub.substitute_in_text("${MISSING}")


def test_substitute_empty_string_value() -> None:
    """Test substitution with empty string value."""
    sub = EnvironmentSubstitutor({"EMPTY": ""})
    result = sub.substitute_in_text("Value: ${EMPTY}.")
    assert result == "Value: ."


def test_substitute_in_data_string() -> None:
    """Test data substitution with string."""
    sub = EnvironmentSubstitutor({"VAR": "value"})
    result = sub.substitute_in_data("${VAR}")
    assert result == "value"


def test_substitute_in_data_list() -> None:
    """Test data substitution with list."""
    sub = EnvironmentSubstitutor({"HOST": "localhost", "PORT": "5432"})
    data = ["${HOST}", "${PORT}", "static"]
    result = sub.substitute_in_data(data)
    assert result == ["localhost", "5432", "static"]


def test_substitute_in_data_dict() -> None:
    """Test data substitution with dictionary."""
    sub = EnvironmentSubstitutor({"USER": "admin", "PASS": "secret"})
    data = {"username": "${USER}", "password": "${PASS}", "timeout": 30}
    result = sub.substitute_in_data(data)
    assert result == {"username": "admin", "password": "secret", "timeout": 30}


def test_substitute_in_data_nested() -> None:
    """Test data substitution with nested structures."""
    sub = EnvironmentSubstitutor({"DB_HOST": "db.example.com", "DB_PORT": "5432"})
    data = {
        "database": {
            "host": "${DB_HOST}",
            "port": "${DB_PORT}",
            "settings": ["option1", "${DB_HOST}"],
        }
    }
    result = sub.substitute_in_data(data)
    assert result == {
        "database": {
            "host": "db.example.com",
            "port": "5432",
            "settings": ["option1", "db.example.com"],
        }
    }


def test_substitute_in_data_preserves_non_strings() -> None:
    """Test that non-string values are preserved."""
    sub = EnvironmentSubstitutor({"VAR": "value"})
    data = {"int": 42, "float": 3.14, "bool": True, "none": None}
    result = sub.substitute_in_data(data)
    assert result == {"int": 42, "float": 3.14, "bool": True, "none": None}


def test_substitute_partial_replacement() -> None:
    """Test substitution with partial string replacement."""
    sub = EnvironmentSubstitutor({"HOST": "localhost", "PORT": "8080"})
    result = sub.substitute_in_text("http://${HOST}:${PORT}/api")
    assert result == "http://localhost:8080/api"


def test_substitute_default_with_colon() -> None:
    """Test substitution with default containing colon."""
    sub = EnvironmentSubstitutor({})
    result = sub.substitute_in_text("${VAR:http://default:8080}")
    assert result == "http://default:8080"


def test_substitute_special_characters() -> None:
    """Test substitution with special characters in values."""
    sub = EnvironmentSubstitutor({"PATH": "/usr/local/bin", "SPECIAL": "a@b#c$d"})
    result = sub.substitute_in_text("${PATH} ${SPECIAL}")
    assert result == "/usr/local/bin a@b#c$d"


def test_substitute_dollar_sign_without_brace() -> None:
    """Test that $ without { is not treated as placeholder."""
    sub = EnvironmentSubstitutor({})
    result = sub.substitute_in_text("Price: $100")
    assert result == "Price: $100"


def test_substitute_multiple_in_same_string() -> None:
    """Test multiple substitutions in same string."""
    sub = EnvironmentSubstitutor({"A": "alpha", "B": "beta", "C": "gamma"})
    result = sub.substitute_in_text("${A}-${B}-${C}")
    assert result == "alpha-beta-gamma"


def test_substitute_environment_from_os_environ(monkeypatch) -> None:
    """Test that EnvironmentSubstitutor uses os.environ by default."""
    monkeypatch.setenv("TEST_VAR", "from_env")
    sub = EnvironmentSubstitutor()
    result = sub.substitute_in_text("${TEST_VAR}")
    assert result == "from_env"


def test_substitute_empty_list() -> None:
    """Test substitution with empty list."""
    sub = EnvironmentSubstitutor({})
    result = sub.substitute_in_data([])
    assert result == []


def test_substitute_empty_dict() -> None:
    """Test substitution with empty dict."""
    sub = EnvironmentSubstitutor({})
    result = sub.substitute_in_data({})
    assert result == {}

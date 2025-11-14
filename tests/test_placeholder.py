"""Smoke tests for the package exports."""

from queryhub import ConfigLoader, EmailClient, ReportExecutor


def test_public_api() -> None:
    """Validate that top-level imports remain available."""

    assert ConfigLoader is not None
    assert EmailClient is not None
    assert ReportExecutor is not None

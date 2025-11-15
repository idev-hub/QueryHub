"""Tests for email client components."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from queryhub.config.models import (
    ComponentRenderConfig,
    ComponentRendererType,
    QueryComponentConfig,
    ReportConfig,
    ReportEmailConfig,
    SMTPConfig,
)
from queryhub.email.client import (
    MessageBuilder,
    RecipientResolver,
    SubjectFormatter,
)
from queryhub.services import ReportExecutionResult


def _create_test_report(
    report_id: str = "test_report",
    title: str = "Test Report",
    email_config: ReportEmailConfig | None = None,
) -> ReportConfig:
    """Helper to create test report config."""
    return ReportConfig(
        id=report_id,
        title=title,
        components=[
            QueryComponentConfig(
                id="test_component",
                provider="test_provider",
                query={},
                render=ComponentRenderConfig(type=ComponentRendererType.TABLE, options={}),
            )
        ],
        email=email_config,
    )


def _create_test_result(
    report: ReportConfig,
    html: str = "<html><body>Test</body></html>",
    has_failures: bool = False,
) -> ReportExecutionResult:
    """Helper to create test execution result."""
    from queryhub.services.component_executor import ComponentExecutionResult
    from queryhub.providers.base_query_provider import QueryResult
    
    components = []
    if has_failures:
        # Create a failed component
        mock_component = QueryComponentConfig(
            id="failed_comp",
            provider="test_provider",
            query={},
            render=ComponentRenderConfig(type=ComponentRendererType.TABLE, options={}),
        )
        failed_result = ComponentExecutionResult(
            component=mock_component,
            result=None,
            rendered_html=None,
            error=Exception("Test error"),
            attempts=1,
            duration_seconds=0.1,
        )
        components.append(failed_result)
    else:
        # Create a successful component
        success_component = QueryComponentConfig(
            id="success_comp",
            provider="test_provider",
            query={},
            render=ComponentRenderConfig(type=ComponentRendererType.TABLE, options={}),
        )
        success_result = ComponentExecutionResult(
            component=success_component,
            result=QueryResult(data=[{"col1": "value1"}]),
            rendered_html="<table></table>",
            error=None,
            attempts=1,
            duration_seconds=0.1,
        )
        components.append(success_result)
    
    return ReportExecutionResult(
        report=report,
        html=html,
        components=components,
        generated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        metadata={"failures": ["comp1"] if has_failures else []},
    )


def test_recipient_resolver_from_report() -> None:
    """Test RecipientResolver resolves recipients from report config."""
    smtp_config = SMTPConfig(host="localhost", port=587)
    resolver = RecipientResolver(smtp_config)

    email_config = ReportEmailConfig(
        to=["user1@example.com", "user2@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
    )
    report = _create_test_report(email_config=email_config)

    to, cc, bcc = resolver.resolve(report, None)

    assert to == ["user1@example.com", "user2@example.com"]
    assert cc == ["cc@example.com"]
    assert bcc == ["bcc@example.com"]


def test_recipient_resolver_from_smtp_default() -> None:
    """Test RecipientResolver uses SMTP default when no report config."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_to=["default@example.com"],
    )
    resolver = RecipientResolver(smtp_config)
    report = _create_test_report()

    to, cc, bcc = resolver.resolve(report, None)

    assert to == ["default@example.com"]
    assert cc == []
    assert bcc == []


def test_recipient_resolver_with_overrides() -> None:
    """Test RecipientResolver prioritizes overrides."""
    smtp_config = SMTPConfig(host="localhost", port=587)
    resolver = RecipientResolver(smtp_config)

    email_config = ReportEmailConfig(to=["original@example.com"])
    report = _create_test_report(email_config=email_config)

    overrides = ReportEmailConfig(
        to=["override@example.com"],
        cc=["override_cc@example.com"],
    )

    to, cc, bcc = resolver.resolve(report, overrides)

    assert to == ["override@example.com"]
    assert cc == ["override_cc@example.com"]


def test_recipient_resolver_no_recipients_error() -> None:
    """Test RecipientResolver raises error when no recipients configured."""
    from queryhub.core.errors import EmailError

    smtp_config = SMTPConfig(host="localhost", port=587)
    resolver = RecipientResolver(smtp_config)
    report = _create_test_report()

    with pytest.raises(EmailError, match="No email recipients configured"):
        resolver.resolve(report, None)


def test_recipient_resolver_normalize_addresses() -> None:
    """Test RecipientResolver normalizes addresses (strips whitespace)."""
    smtp_config = SMTPConfig(host="localhost", port=587)
    resolver = RecipientResolver(smtp_config)

    email_config = ReportEmailConfig(
        to=[" user1@example.com ", "user2@example.com", "  ", ""],
    )
    report = _create_test_report(email_config=email_config)

    to, cc, bcc = resolver.resolve(report, None)

    assert to == ["user1@example.com", "user2@example.com"]


def test_subject_formatter_default_template() -> None:
    """Test SubjectFormatter with default template."""
    # Configure SMTP with Jinja2-style default template
    smtp_config = SMTPConfig(host="localhost", port=587, subject_template="{{ title }}")
    formatter = SubjectFormatter(smtp_config)

    report = _create_test_report(title="Daily Sales Report")
    result = _create_test_result(report)

    subject = formatter.format(report, result, None)

    assert subject == "Daily Sales Report"


def test_subject_formatter_custom_template() -> None:
    """Test SubjectFormatter with custom template from SMTP config."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        subject_template="[Report] {{ title }} - {{ generated_at.strftime('%Y-%m-%d') }}",
    )
    formatter = SubjectFormatter(smtp_config)

    report = _create_test_report(title="Sales")
    result = _create_test_result(report)

    subject = formatter.format(report, result, None)

    assert "[Report] Sales - 2024-01-01" == subject


def test_subject_formatter_report_template() -> None:
    """Test SubjectFormatter with template from report config."""
    smtp_config = SMTPConfig(host="localhost", port=587)
    formatter = SubjectFormatter(smtp_config)

    email_config = ReportEmailConfig(
        to=["user@example.com"],
        subject_template="Report: {{ title }} - {% if has_failures %}FAILED{% else %}SUCCESS{% endif %}",
    )
    report = _create_test_report(title="Test", email_config=email_config)
    result = _create_test_result(report, has_failures=False)

    subject = formatter.format(report, result, None)

    assert "Report: Test - SUCCESS" == subject


def test_subject_formatter_override_template() -> None:
    """Test SubjectFormatter with override template."""
    smtp_config = SMTPConfig(host="localhost", port=587)
    formatter = SubjectFormatter(smtp_config)

    report = _create_test_report(title="Test")
    result = _create_test_result(report)

    overrides = ReportEmailConfig(
        to=["user@example.com"],
        subject_template="Override: {{ title }}",
    )

    subject = formatter.format(report, result, overrides)

    assert subject == "Override: Test"


def test_message_builder_basic() -> None:
    """Test MessageBuilder creates basic email message."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="sender@example.com",
        default_to=["recipient@example.com"],
        subject_template="{{ title }}",
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    report = _create_test_report(title="Test Report")
    result = _create_test_result(report, html="<html>Content</html>")

    message = builder.build(result, None)

    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "Test Report"
    assert "<html>Content</html>" in str(message)


def test_message_builder_with_cc() -> None:
    """Test MessageBuilder includes CC recipients."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="sender@example.com",
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    email_config = ReportEmailConfig(
        to=["recipient@example.com"],
        cc=["cc1@example.com", "cc2@example.com"],
    )
    report = _create_test_report(email_config=email_config)
    result = _create_test_result(report)

    message = builder.build(result, None)

    assert message["Cc"] == "cc1@example.com, cc2@example.com"


def test_message_builder_with_bcc() -> None:
    """Test MessageBuilder includes BCC recipients."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="sender@example.com",
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    email_config = ReportEmailConfig(
        to=["recipient@example.com"],
        bcc=["bcc@example.com"],
    )
    report = _create_test_report(email_config=email_config)
    result = _create_test_result(report)

    message = builder.build(result, None)

    assert message["Bcc"] == "bcc@example.com"


def test_message_builder_with_reply_to() -> None:
    """Test MessageBuilder includes Reply-To header."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="sender@example.com",
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    email_config = ReportEmailConfig(to=["recipient@example.com"])
    report = _create_test_report(email_config=email_config)
    result = _create_test_result(report)

    overrides = ReportEmailConfig(
        to=["recipient@example.com"],
        reply_to="replyto@example.com",
    )

    message = builder.build(result, overrides)

    assert message["Reply-To"] == "replyto@example.com"


def test_message_builder_from_override() -> None:
    """Test MessageBuilder uses from address override."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="default@example.com",
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    email_config = ReportEmailConfig(to=["recipient@example.com"])
    report = _create_test_report(email_config=email_config)
    result = _create_test_result(report)

    overrides = ReportEmailConfig(
        to=["recipient@example.com"],
        from_address="override@example.com",
    )

    message = builder.build(result, overrides)

    assert message["From"] == "override@example.com"


def test_message_builder_missing_from_address() -> None:
    """Test MessageBuilder raises error when from address is missing."""
    from queryhub.core.errors import EmailError

    smtp_config = SMTPConfig(host="localhost", port=587)

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    email_config = ReportEmailConfig(to=["recipient@example.com"])
    report = _create_test_report(email_config=email_config)
    result = _create_test_result(report)

    with pytest.raises(EmailError, match="SMTP configuration missing 'default_from' address"):
        builder.build(result, None)


def test_message_builder_plain_text_body() -> None:
    """Test MessageBuilder creates plain text body."""
    smtp_config = SMTPConfig(
        host="localhost",
        port=587,
        default_from="sender@example.com",
        default_to=["recipient@example.com"],
    )

    resolver = RecipientResolver(smtp_config)
    formatter = SubjectFormatter(smtp_config)
    builder = MessageBuilder(smtp_config, resolver, formatter)

    report = _create_test_report(title="Test Report")
    result = _create_test_result(report, has_failures=True)

    message = builder.build(result, None)

    plain_content = str(message)
    assert "Report: Test Report" in plain_content
    assert "Generated at: 2024-01-01" in plain_content

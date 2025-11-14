"""SMTP email client for delivering reports."""

from __future__ import annotations

import logging
from email.message import EmailMessage
from email.utils import getaddresses
from typing import Sequence

from jinja2 import Template

from ..config.models import ReportConfig, ReportEmailConfig, SMTPConfig
from ..core.contracts import EmailSenderProtocol
from ..core.errors import EmailError
from ..services import ReportExecutionResult

_LOGGER = logging.getLogger(__name__)


class RecipientResolver:
    """Resolve email recipients from configuration (SRP)."""

    def __init__(self, smtp_config: SMTPConfig) -> None:
        self._smtp_config = smtp_config

    def resolve(
        self,
        report: ReportConfig,
        overrides: ReportEmailConfig | None,
    ) -> tuple[list[str], list[str], list[str]]:
        """Resolve to, cc, and bcc recipients."""
        report_email = report.email

        to_candidates = (
            overrides.to if overrides and overrides.to else None
        ) or (report_email.to if report_email and report_email.to else None) or self._smtp_config.default_to

        if not to_candidates:
            raise EmailError("No email recipients configured")

        cc_candidates = (
            overrides.cc if overrides and overrides.cc else None
        ) or (report_email.cc if report_email and report_email.cc else None)

        bcc_candidates = (
            overrides.bcc if overrides and overrides.bcc else None
        ) or (report_email.bcc if report_email and report_email.bcc else None)

        return (
            self._normalize_addresses(to_candidates),
            self._normalize_addresses(cc_candidates),
            self._normalize_addresses(bcc_candidates),
        )

    @staticmethod
    def _normalize_addresses(addresses: Sequence[str] | None) -> list[str]:
        """Normalize and filter email addresses."""
        return [addr.strip() for addr in (addresses or []) if addr and addr.strip()]


class SubjectFormatter:
    """Format email subject lines (SRP)."""

    def __init__(self, smtp_config: SMTPConfig) -> None:
        self._smtp_config = smtp_config

    def format(
        self,
        report: ReportConfig,
        result: ReportExecutionResult,
        overrides: ReportEmailConfig | None,
    ) -> str:
        """Format subject line using template."""
        template_text = (
            (overrides.subject_template if overrides else None)
            or (report.email.subject_template if report.email else None)
            or self._smtp_config.subject_template
            or "{title}"
        )

        template = Template(template_text)
        context = {
            "title": report.title,
            "report": report,
            "result": result,
            "generated_at": result.generated_at,
            "has_failures": result.has_failures,
        }
        return template.render(context)


class MessageBuilder:
    """Build email messages (SRP)."""

    def __init__(
        self,
        smtp_config: SMTPConfig,
        recipient_resolver: RecipientResolver,
        subject_formatter: SubjectFormatter,
    ) -> None:
        self._smtp_config = smtp_config
        self._recipient_resolver = recipient_resolver
        self._subject_formatter = subject_formatter

    def build(
        self,
        result: ReportExecutionResult,
        overrides: ReportEmailConfig | None,
    ) -> EmailMessage:
        """Build complete email message."""
        report = result.report
        to_recipients, cc_recipients, bcc_recipients = self._recipient_resolver.resolve(
            report, overrides
        )
        subject = self._subject_formatter.format(report, result, overrides)
        from_address = self._resolve_from_address(overrides)

        message = EmailMessage()
        message["From"] = from_address
        message["To"] = ", ".join(to_recipients)
        
        if cc_recipients:
            message["Cc"] = ", ".join(cc_recipients)
        
        if overrides and overrides.reply_to:
            message["Reply-To"] = overrides.reply_to
        
        if bcc_recipients:
            # Include Bcc for testing/debugging (removed before sending)
            message["Bcc"] = ", ".join(bcc_recipients)
        
        message["Subject"] = subject

        plain_text = self._build_plain_text(result)
        message.set_content(plain_text)
        message.add_alternative(result.html, subtype="html")

        return message

    def _resolve_from_address(self, overrides: ReportEmailConfig | None) -> str:
        """Resolve from address."""
        from_address = (
            (overrides.from_address if overrides else None)
            or self._smtp_config.default_from
        )
        if not from_address:
            raise EmailError("SMTP configuration missing 'default_from' address")
        return from_address

    def _build_plain_text(self, result: ReportExecutionResult) -> str:
        """Build plain text email body."""
        lines = [
            f"Report: {result.report.title}",
            f"Generated at: {result.generated_at.isoformat()}",
        ]
        
        if result.metadata.get("failures"):
            failures = ", ".join(result.metadata["failures"])
            lines.append(f"Components with errors: {failures}")
        
        lines.append("\nHTML content attached as alternative body")
        return "\n".join(lines)


class EmailClient(EmailSenderProtocol):
    """SMTP client for sending reports (Facade Pattern)."""

    def __init__(self, smtp_config: SMTPConfig) -> None:
        self._config = smtp_config
        self._recipient_resolver = RecipientResolver(smtp_config)
        self._subject_formatter = SubjectFormatter(smtp_config)
        self._message_builder = MessageBuilder(
            smtp_config,
            self._recipient_resolver,
            self._subject_formatter,
        )

    async def send_report(
        self,
        result: ReportExecutionResult,
        *,
        overrides: ReportEmailConfig | None = None,
    ) -> None:
        """Send report via SMTP."""
        message = self._message_builder.build(result, overrides)
        await self._send_message(message)

    async def _send_message(self, message: EmailMessage) -> None:
        """Send email message via SMTP."""
        try:
            import aiosmtplib
        except ImportError as exc:
            raise EmailError("aiosmtplib dependency missing") from exc

        # Extract all recipients
        recipients = self._extract_all_recipients(message)
        
        # Remove Bcc header before sending (RFC compliance)
        if "Bcc" in message:
            del message["Bcc"]

        try:
            await aiosmtplib.send(
                message,
                hostname=self._config.host,
                port=self._config.port,
                start_tls=self._config.starttls,
                use_tls=self._config.use_tls,
                username=self._config.username or self._config.auth.username,
                password=self._resolve_password(),
                timeout=self._config.timeout_seconds,
                recipients=recipients if recipients else None,
            )
        except Exception as exc:
            raise EmailError(f"Failed to send email: {exc}") from exc

    def _extract_all_recipients(self, message: EmailMessage) -> list[str]:
        """Extract all recipient addresses from message."""
        to_recipients = message.get_all("To", [])
        cc_recipients = message.get_all("Cc", [])
        bcc_recipients = message.get_all("Bcc", [])
        
        parsed = getaddresses([*to_recipients, *cc_recipients, *bcc_recipients])
        return [addr for _, addr in parsed if addr]

    def _resolve_password(self) -> str | None:
        """Resolve SMTP password from config."""
        if self._config.password:
            return self._config.password.get_secret_value()
        if self._config.auth.password:
            return self._config.auth.password.get_secret_value()
        return None

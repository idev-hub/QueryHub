"""SMTP email client for delivering reports."""

from __future__ import annotations

import logging
from email.message import EmailMessage
from email.utils import getaddresses
from typing import Iterable, Sequence

from jinja2 import Template

from ..config.models import ReportConfig, ReportEmailConfig, SMTPConfig
from ..services import ReportExecutionResult

_LOGGER = logging.getLogger(__name__)


class EmailClient:
    """Wrapper around aiosmtplib with configuration awareness."""

    def __init__(self, smtp_config: SMTPConfig) -> None:
        self._config = smtp_config

    async def send_report(
        self,
        result: ReportExecutionResult,
        *,
        overrides: ReportEmailConfig | None = None,
    ) -> None:
        message = self._build_message(result, overrides=overrides)
        await self._send(message)

    def _build_message(
        self,
        result: ReportExecutionResult,
        *,
        overrides: ReportEmailConfig | None,
    ) -> EmailMessage:
        report = result.report
        to_recipients, cc_recipients, bcc_recipients = self._resolve_recipients(report, overrides)
        subject = self._resolve_subject(report, result, overrides)
        from_address = (overrides.from_address if overrides else None) or self._config.default_from
        if not from_address:
            raise ValueError("SMTP configuration missing 'default_from' address")

        message = EmailMessage()
        message["From"] = from_address
        message["To"] = ", ".join(to_recipients)
        if cc_recipients:
            message["Cc"] = ", ".join(cc_recipients)
        if overrides and overrides.reply_to:
            message["Reply-To"] = overrides.reply_to
        if bcc_recipients:
            # RFC-compliant email clients omit Bcc headers automatically; we include it so tests can assert recipients.
            message["Bcc"] = ", ".join(bcc_recipients)
        message["Subject"] = subject

        plain_text = self._build_plain_text(result)
        message.set_content(plain_text)
        message.add_alternative(result.html, subtype="html")

        self._apply_dkim_stub(message)
        return message

    def _resolve_recipients(
        self, report: ReportConfig, overrides: ReportEmailConfig | None
    ) -> tuple[list[str], list[str], list[str]]:
        def _normalise(values: Iterable[str] | None) -> list[str]:
            return [addr for addr in (values or []) if addr]

        report_email = report.email

        to_candidates = (
            overrides.to if overrides and overrides.to else None
        ) or (
            report_email.to if report_email and report_email.to else None
        ) or self._config.default_to
        to_addresses = _normalise(to_candidates)
        if not to_addresses:
            raise ValueError("No email recipients configured")

        cc_candidates = (
            overrides.cc if overrides and overrides.cc else None
        ) or (report_email.cc if report_email and report_email.cc else None)
        bcc_candidates = (
            overrides.bcc if overrides and overrides.bcc else None
        ) or (report_email.bcc if report_email and report_email.bcc else None)

        return to_addresses, _normalise(cc_candidates), _normalise(bcc_candidates)

    def _resolve_subject(
        self,
        report: ReportConfig,
        result: ReportExecutionResult,
        overrides: ReportEmailConfig | None,
    ) -> str:
        template_text = (
            (overrides.subject_template if overrides else None)
            or (report.email.subject_template if report.email else None)
            or self._config.subject_template
            or "{title}"
        )
        template = Template(template_text)
        context = {
            "title": report.title,
            "report": report,
            "result": result,
            "generated_at": result.generated_at,
        }
        return template.render(context)

    def _build_plain_text(self, result: ReportExecutionResult) -> str:
        lines = [f"Report: {result.report.title}", f"Generated at: {result.generated_at.isoformat()}" ]
        if result.metadata.get("failures"):
            failures = ", ".join(result.metadata["failures"])
            lines.append(f"Components with errors: {failures}")
        lines.append("\nHTML content attached as alternative body")
        return "\n".join(lines)

    async def _send(self, message: EmailMessage) -> None:
        try:
            import aiosmtplib
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError("aiosmtplib dependency missing") from exc

        to_recipients = message.get_all("To", [])
        cc_recipients = message.get_all("Cc", [])
        bcc_recipients = message.get_all("Bcc", [])
        if "Bcc" in message:
            del message["Bcc"]
        parsed = getaddresses([*to_recipients, *cc_recipients, *bcc_recipients])
        all_recipients = [addr for _, addr in parsed if addr]

        await aiosmtplib.send(
            message,
            hostname=self._config.host,
            port=self._config.port,
            start_tls=self._config.starttls,
            use_tls=self._config.use_tls,
            username=self._config.username or self._config.auth.username,
            password=(
                (self._config.password.get_secret_value() if self._config.password else None)
                or (
                    self._config.auth.password.get_secret_value()
                    if self._config.auth.password
                    else None
                )
            ),
            timeout=self._config.timeout_seconds,
            recipients=all_recipients if all_recipients else None,
        )

    def _apply_dkim_stub(self, message: EmailMessage) -> None:
        key_path = self._config.auth.dkim_private_key_path
        if not key_path:
            return
        _LOGGER.info(
            "DKIM signing requested via %s but not implemented; skipping signature",
            key_path,
        )

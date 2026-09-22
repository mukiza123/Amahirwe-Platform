"""Outbound email over authenticated SMTP (Gmail by default).

Deliberately plain smtplib/email — no third-party mail SDK — since a
verification code is a one-line plain-text message and Python's
standard library already does everything this needs.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Sends a plain-text email. Raises on failure — callers that can't
    afford to fail the whole request over a transient SMTP hiccup
    (e.g. registration, where the account is already committed) should
    catch this themselves rather than this function swallowing it."""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_username}>"
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def send_email_safely(to: str, subject: str, body: str) -> bool:
    """Same as send_email, but swallows failures into a False return
    instead of raising — for callers where the underlying action (e.g.
    account creation) already succeeded and shouldn't be undone just
    because the follow-up email didn't go out. Returns True on success."""

    try:
        send_email(to, subject, body)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False

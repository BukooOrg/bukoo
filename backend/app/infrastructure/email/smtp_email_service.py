"""
SMTP email service using aiosmtplib.
Connects to Mailpit in development, a real SMTP server in production.
"""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import get_configs


class SMTPEmailService:
    async def send(self, to: str, subject: str, body_html: str) -> None:
        configs = get_configs()
        message = MIMEMultipart("alternative")
        message["From"] = configs.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body_html, "html"))

        await aiosmtplib.send(
            message,
            hostname=configs.SMTP_HOST,
            port=configs.SMTP_PORT,
            username=configs.SMTP_USERNAME or None,
            password=configs.SMTP_PASSWORD or None,
            use_tls=configs.SMTP_TLS,
        )

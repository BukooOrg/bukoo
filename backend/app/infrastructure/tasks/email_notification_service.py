from __future__ import annotations

from typing import override

import structlog

from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.core.config import get_configs
from app.infrastructure.tasks.email_tasks import send_mail

logger = structlog.get_logger(__name__)


class CeleryEmailNotificationService(IEmailNotificationService):
    @override
    def send_welcome(self, to: str, full_name: str) -> None:
        configs = get_configs()
        send_mail.delay(
            to=to,
            subject=f"Welcome to {configs.APP_NAME.capitalize()}!",
            body_html=(
                f"<h1>Welcome, {full_name}!</h1>"
                f"<p>Your account has been created. Please verify your email to get started.</p>"
            ),
        )

    @override
    def send_verification_email(self, to: str, otp: str) -> None:
        send_mail.delay(
            to=to,
            subject="Verify your email address",
            body_html=(
                f"<h1>Email Verification</h1>"
                f"<p>Your verification code is: <strong>{otp}</strong></p>"
                f"<p>This code expires in 15 minutes.</p>"
            ),
        )

    @override
    def send_password_reset_email(self, to: str, otp: str) -> None:
        send_mail.delay(
            to=to,
            subject="Reset your password",
            body_html=(
                f"<h1>Password Reset</h1>"
                f"<p>Your password reset code is: <strong>{otp}</strong></p>"
                f"<p>This code expires in 15 minutes.</p>"
            ),
        )

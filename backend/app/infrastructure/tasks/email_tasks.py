from __future__ import annotations

import asyncio
from typing import Any

from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.infrastructure.tasks.celery_app import celery_app


@celery_app.task(
    name="email.send_mail",
    queue="mail",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_mail(self: Any, to: str, subject: str, body_html: str) -> None:
    try:
        asyncio.run(
            SMTPEmailService().send(to=to, subject=subject, body_html=body_html)
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries * 60) from exc

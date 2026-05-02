from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import get_configs

_DEFAULT_EXCHANGE = Exchange("default", type="direct")
_MAIL_EXCHANGE = Exchange("mail", type="direct")

TASK_QUEUES = (
    Queue("default", _DEFAULT_EXCHANGE, routing_key="default"),
    Queue("mail", _MAIL_EXCHANGE, routing_key="mail"),
)

TASK_ROUTES = {
    "email.*": {"queue": "mail", "routing_key": "mail"},
}


def create_celery() -> Celery:
    tasks = ["app.infrastructure.tasks.email_tasks"]

    configs = get_configs()
    app = Celery(
        configs.APP_NAME,
        broker=configs.REDIS_URL,
        backend=configs.REDIS_URL,
        include=tasks,
    )
    app.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Time
        timezone="UTC",
        enable_utc=True,
        # Queues & routing
        task_queues=TASK_QUEUES,
        task_default_queue="default",
        task_default_exchange="default",
        task_default_routing_key="default",
        task_routes=TASK_ROUTES,
        # Reliability
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        # Time limits (seconds)
        task_soft_time_limit=300,
        task_time_limit=360,
        # Result expiry
        result_expires=3600,
        # Broker
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = create_celery()

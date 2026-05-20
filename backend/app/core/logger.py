"""Logging configuration for the application."""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

import sqlparse
import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.types import EventDict, Processor

from app.core.config import get_configs

logger = structlog.get_logger()


def format_sql(statement: str) -> str:
    return sqlparse.format(statement, reindent=True, keyword_case="upper")


def format_sql_processor(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Beautify SQL statements in SQLAlchemy log events."""
    logger_name = event_dict.get("logger", "")
    if "sqlalchemy.engine" in logger_name:
        event = event_dict.get("event", "")
        if event and any(
            kw in event.upper()
            for kw in ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")
        ):
            event_dict["event"] = (
                "\n\n"
                + sqlparse.format(
                    event,
                    reindent=True,
                    keyword_case="upper",
                    indent_width=2,
                )
                + "\n\n"
            )
    return event_dict


def drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Uvicorn adds `color_message` which duplicates `event`.

    Remove it to avoid double logging.
    """
    event_dict.pop("color_message", None)
    return event_dict


def file_log_filter_processors(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Filter out the request ID, path, method, client host, and status code from the event dict if the
    corresponding setting is False."""

    configs = get_configs()

    if not configs.FILE_LOG_INCLUDE_REQUEST_ID:
        event_dict.pop("request_id", None)
    if not configs.FILE_LOG_INCLUDE_PATH:
        event_dict.pop("path", None)
    if not configs.FILE_LOG_INCLUDE_METHOD:
        event_dict.pop("method", None)
    if not configs.FILE_LOG_INCLUDE_CLIENT_HOST:
        event_dict.pop("client_host", None)
    if not configs.FILE_LOG_INCLUDE_STATUS_CODE:
        event_dict.pop("status_code", None)
    return event_dict


def console_log_filter_processors(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Filter out the request ID, path, method, client host, and status code from the event dict if the
    corresponding setting is False."""

    configs = get_configs()

    if not configs.CONSOLE_LOG_INCLUDE_REQUEST_ID:
        event_dict.pop("request_id", None)
    if not configs.CONSOLE_LOG_INCLUDE_PATH:
        event_dict.pop("path", None)
    if not configs.CONSOLE_LOG_INCLUDE_METHOD:
        event_dict.pop("method", None)
    if not configs.CONSOLE_LOG_INCLUDE_CLIENT_HOST:
        event_dict.pop("client_host", None)
    if not configs.CONSOLE_LOG_INCLUDE_STATUS_CODE:
        event_dict.pop("status_code", None)
    return event_dict


# Shared processors for all loggers
timestamper = structlog.processors.TimeStamper(fmt="iso")
SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.stdlib.ExtraAdder(),
    drop_color_message_key,
    format_sql_processor,
    timestamper,
    structlog.processors.StackInfoRenderer(),
]


# Configure structlog globally
structlog.configure(
    processors=SHARED_PROCESSORS
    + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def build_formatter(
    *, json_output: bool, pre_chain: list[Processor]
) -> structlog.stdlib.ProcessorFormatter:
    """Build a ProcessorFormatter with the specified renderer and processors."""
    renderer = JSONRenderer() if json_output else ConsoleRenderer()

    processors = [structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer]

    if json_output:
        pre_chain = pre_chain + [structlog.processors.format_exc_info]

    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=pre_chain, processors=processors
    )


# Setup log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

configs = get_configs()

# File handler configuration
file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, "app.log"),
    maxBytes=configs.FILE_LOG_MAX_BYTES,
    backupCount=configs.FILE_LOG_BACKUP_COUNT,
)
file_handler.setLevel(configs.FILE_LOG_LEVEL)
file_handler.setFormatter(
    build_formatter(
        json_output=configs.FILE_LOG_FORMAT_JSON,
        pre_chain=SHARED_PROCESSORS + [file_log_filter_processors],
    )
)

# Console handler configuration
console_handler = logging.StreamHandler()
console_handler.setLevel(configs.CONSOLE_LOG_LEVEL)
console_handler.setFormatter(
    build_formatter(
        json_output=configs.CONSOLE_LOG_FORMAT_JSON,
        pre_chain=SHARED_PROCESSORS + [console_log_filter_processors],
    )
)


# Root logger configuration
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()  # avoid duplicate logs
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Uvicorn logger integration
for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.propagate = True
    logger.setLevel(logging.INFO)

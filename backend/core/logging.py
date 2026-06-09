"""
Structured logging setup using structlog + rich.
All modules import `logger` from here.
"""
from __future__ import annotations

import logging
import sys

import structlog
from rich.logging import RichHandler

from backend.core.config import settings


def setup_logging() -> None:
    """Configure structlog with rich console output."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )


logger = structlog.get_logger("omclaw")

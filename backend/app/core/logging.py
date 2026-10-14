import logging
import sys
from typing import Any, cast

import structlog
from structlog.types import FilteringBoundLogger


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for structured JSON logging."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Get a structured logger instance."""
    return cast(FilteringBoundLogger, structlog.get_logger(name))


class RequestLogger:
    """Logger for HTTP requests with request_id context."""

    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str,
        **extra: Any,
    ) -> None:
        self.logger.info(
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
            **extra,
        )

    def log_error(
        self,
        method: str,
        path: str,
        error: str,
        request_id: str,
        **extra: Any,
    ) -> None:
        self.logger.error(
            "http_error",
            method=method,
            path=path,
            error=error,
            request_id=request_id,
            **extra,
        )

import logging

import structlog
from structlog.typing import FilteringBoundLogger

configured = False


def configure_logging(log_level: str = "INFO") -> None:
    global configured
    if configured:
        return
    level = getattr(logging, log_level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    configured = True


def get_logger(name: str) -> FilteringBoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]


class RequestLogger:
    def __init__(self, logger: FilteringBoundLogger) -> None:
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str,
    ) -> None:
        self.logger.info(
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

    def log_error(self, method: str, path: str, error: str, request_id: str) -> None:
        self.logger.error(
            "http_error",
            method=method,
            path=path,
            error=error,
            request_id=request_id,
        )

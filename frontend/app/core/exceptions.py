from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger

logger = get_logger("exceptions")


class AppException(Exception):
    def __init__(self, detail: str, code: str, status_code: int = 400):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("app_exception", code=exc.code, detail=exc.detail, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.warning("validation_error", errors=exc.errors(), path=request.url.path)
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación",
            "code": "validation_error",
            "errors": exc.errors(),
        },
    )


async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("integrity_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflicto de integridad", "code": "integrity_error"},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "code": "internal_server_error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, integrity_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)

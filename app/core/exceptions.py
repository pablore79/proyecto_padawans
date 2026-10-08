from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import settings


class AppException(Exception):
    def __init__(
        self,
        detail: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        extra: dict[str, Any] | None = None,
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, detail: str, code: str = "not_found", extra: dict[str, Any] | None = None):
        super().__init__(detail, code, status.HTTP_404_NOT_FOUND, extra)


class ConflictError(AppException):
    def __init__(self, detail: str, code: str = "conflict", extra: dict[str, Any] | None = None):
        super().__init__(detail, code, status.HTTP_409_CONFLICT, extra)


class UnauthorizedError(AppException):
    def __init__(
        self, detail: str, code: str = "unauthorized", extra: dict[str, Any] | None = None
    ):
        super().__init__(detail, code, status.HTTP_401_UNAUTHORIZED, extra)


class ForbiddenError(AppException):
    def __init__(self, detail: str, code: str = "forbidden", extra: dict[str, Any] | None = None):
        super().__init__(detail, code, status.HTTP_403_FORBIDDEN, extra)


ERROR_CODES = {
    "dni_duplicado": "Ya existe un alumno con ese DNI",
    "email_duplicado": "Ya existe un alumno con ese email",
    "usuario_duplicado": "Ya existe un usuario con ese username o email",
    "alumno_no_encontrado": "Alumno no encontrado",
    "curso_no_encontrado": "Curso no encontrado",
    "materia_no_encontrada": "Materia no encontrada",
    "inscripcion_no_encontrada": "Inscripción no encontrada",
    "usuario_no_encontrado": "Usuario no encontrado",
    "docente_no_encontrado": "Docente no encontrado",
    "cupos_completos": "El curso ha alcanzado el máximo de cupos",
    "inscripcion_duplicada": "El alumno ya está inscripto activamente en este curso",
    "docente_ya_asignado": "El docente ya está asignado a este curso",
    "rol_alumno_sin_alumno_id": "Un usuario con rol alumno debe tener alumno_id",
    "rol_admin_docente_con_alumno_id": "Un usuario con rol admin o docente no debe tener alumno_id",
    "credenciales_invalidas": "Credenciales inválidas",
    "token_invalido": "Token inválido o expirado",
    "sin_permisos": "No tiene permisos para realizar esta acción",
    "validacion_error": "Error de validación en los datos enviados",
}


def get_error_message(code: str) -> str:
    return ERROR_CODES.get(code, "Error interno del servidor")


def create_error_response(
    detail: str,
    code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    content: dict[str, str | dict[str, Any]] = {"detail": detail, "code": code}
    if extra:
        content["extra"] = extra
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return create_error_response(exc.detail, exc.code, exc.status_code, exc.extra)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
        detail = "; ".join(errors)
        return create_error_response(
            detail, "validacion_error", status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
        detail = "; ".join(errors)
        return create_error_response(
            detail, "validacion_error", status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        error_msg = str(exc.orig).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            if "dni" in error_msg:
                return create_error_response(
                    "Ya existe un alumno con ese DNI", "dni_duplicado", status.HTTP_409_CONFLICT
                )
            if "email" in error_msg:
                return create_error_response(
                    "Ya existe un alumno con ese email", "email_duplicado", status.HTTP_409_CONFLICT
                )
            if "username" in error_msg or "usuarios_email_key" in error_msg:
                return create_error_response(
                    "Ya existe un usuario con ese username o email",
                    "usuario_duplicado",
                    status.HTTP_409_CONFLICT,
                )
            if "inscripciones_alumno_curso_activa" in error_msg:
                return create_error_response(
                    "El alumno ya está inscripto activamente en este curso",
                    "inscripcion_duplicada",
                    status.HTTP_409_CONFLICT,
                )
            if "asignacion_docente_usuario_curso" in error_msg:
                return create_error_response(
                    "El docente ya está asignado a este curso",
                    "docente_ya_asignado",
                    status.HTTP_409_CONFLICT,
                )
            if "cursos_nombre_key" in error_msg:
                return create_error_response(
                    "Ya existe un curso con ese nombre", "curso_duplicado", status.HTTP_409_CONFLICT
                )
        return create_error_response(
            "Error de integridad en la base de datos", "integrity_error", status.HTTP_409_CONFLICT
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if settings.DEBUG:
            import traceback

            traceback.print_exc()
        return create_error_response(
            "Error interno del servidor",
            "internal_server_error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

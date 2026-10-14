from collections.abc import Awaitable, Callable

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models.usuario import Usuario
from app.services.auth_service import AuthService


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Usuario:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Token de autorización requerido", "token_invalido")

    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)


def require_role(*allowed_roles: str) -> Callable[[], Awaitable[Usuario]]:
    async def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol.value not in allowed_roles:
            raise ForbiddenError("No tiene permisos para realizar esta acción", "sin_permisos")
        return current_user

    return role_checker


require_admin = require_role("admin")
require_docente = require_role("docente")
require_alumno = require_role("alumno")
require_admin_or_docente = require_role("admin", "docente")

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_token_data,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.usuario import RolUsuario, Usuario
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.auth import Token, UserCreate, UserRead


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)

    async def register(self, user_data: UserCreate, current_user_id: int) -> UserRead:
        if await self.usuario_repo.exists_username(user_data.username):
            raise ConflictError("Ya existe un usuario con ese username", "usuario_duplicado")
        if await self.usuario_repo.exists_email(user_data.email):
            raise ConflictError("Ya existe un usuario con ese email", "usuario_duplicado")

        if user_data.rol == RolUsuario.ALUMNO and not user_data.alumno_id:
            raise UnauthorizedError(
                "Un usuario con rol alumno debe tener alumno_id", "rol_alumno_sin_alumno_id"
            )
        if user_data.rol in (RolUsuario.ADMIN, RolUsuario.DOCENTE) and user_data.alumno_id:
            raise UnauthorizedError(
                "Un usuario con rol admin o docente no debe tener alumno_id",
                "rol_admin_docente_con_alumno_id",
            )

        user = Usuario(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            rol=user_data.rol,
            alumno_id=user_data.alumno_id,
        )
        created_user = await self.usuario_repo.create(user, current_user_id)
        return UserRead.model_validate(created_user)

    async def login(self, username: str, password: str) -> Token:
        user = await self.usuario_repo.get_by_username(username)
        if not user or not user.activo:
            raise UnauthorizedError("Credenciales inválidas", "credenciales_invalidas")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Credenciales inválidas", "credenciales_invalidas")

        token_data = create_token_data(
            user_id=user.id,
            username=user.username,
            rol=user.rol.value,
            alumno_id=user.alumno_id,
        )
        access_token = create_access_token(token_data)
        return Token(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str) -> Usuario:
        try:
            token_data = decode_access_token(token)
        except ValueError as e:
            raise UnauthorizedError(str(e), "token_invalido") from None

        user = await self.usuario_repo.get(token_data.user_id)
        if not user or not user.activo:
            raise UnauthorizedError("Usuario no encontrado o inactivo", "token_invalido")
        return user

    async def validate_role(self, user: Usuario, allowed_roles: list[str]) -> None:
        if user.rol.value not in allowed_roles:
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError("No tiene permisos para realizar esta acción", "sin_permisos")

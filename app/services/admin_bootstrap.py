from dataclasses import dataclass
from enum import Enum

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import UserCreate


class AdminBootstrapError(Exception):
    """Raised when the initial administrator cannot be created safely."""


class AdminBootstrapStatus(str, Enum):
    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


@dataclass(frozen=True)
class AdminBootstrapResult:
    status: AdminBootstrapStatus
    user: Usuario


# Serializes bootstrap attempts without requiring a schema change.
_ADMIN_BOOTSTRAP_LOCK_KEY = 4_224_004


async def create_initial_admin(
    db: AsyncSession,
    user_data: UserCreate,
) -> AdminBootstrapResult:
    """Create the only administrator allowed through the bootstrap path."""
    if user_data.rol != RolUsuario.ADMIN or user_data.alumno_id is not None:
        raise AdminBootstrapError(
            "El bootstrap solo admite el rol admin y requiere alumno_id nulo."
        )

    await db.execute(select(func.pg_advisory_xact_lock(_ADMIN_BOOTSTRAP_LOCK_KEY)))

    result = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.rol == RolUsuario.ADMIN,
                Usuario.username == user_data.username,
                Usuario.email == str(user_data.email),
            )
        )
    )
    matching_users = list(result.scalars().all())
    admins = [user for user in matching_users if user.rol == RolUsuario.ADMIN]
    same_admin = next(
        (
            user
            for user in admins
            if user.username == user_data.username and user.email == str(user_data.email)
        ),
        None,
    )

    if same_admin is not None and len(admins) == 1:
        return AdminBootstrapResult(AdminBootstrapStatus.ALREADY_EXISTS, same_admin)

    if admins:
        raise AdminBootstrapError(
            "Ya existe otro administrador. Creá administradores adicionales mediante "
            "POST /api/v1/auth/users."
        )

    username_collision = any(user.username == user_data.username for user in matching_users)
    email_collision = any(user.email == str(user_data.email) for user in matching_users)
    if username_collision and email_collision:
        raise AdminBootstrapError(
            "El username y el email ya pertenecen a un usuario que no es administrador."
        )
    if username_collision:
        raise AdminBootstrapError("El username ya pertenece a otro usuario.")
    if email_collision:
        raise AdminBootstrapError("El email ya pertenece a otro usuario.")

    admin = Usuario(
        username=user_data.username,
        email=str(user_data.email),
        password_hash=get_password_hash(user_data.password),
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )
    db.add(admin)
    await db.flush()
    if admin.id is None:
        raise RuntimeError("No se pudo obtener el ID del administrador inicial.")

    admin.created_by = admin.id
    admin.updated_by = admin.id
    await db.flush()
    await db.refresh(admin)
    return AdminBootstrapResult(AdminBootstrapStatus.CREATED, admin)

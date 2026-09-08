
import builtins

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import RolUsuario, Usuario


class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, usuario_id: int) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.id == usuario_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def get_by_alumno_id(self, alumno_id: int) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.alumno_id == alumno_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        rol: RolUsuario | None = None,
        activo: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Usuario]:
        query = select(Usuario)
        if rol:
            query = query.where(Usuario.rol == rol)
        if activo is not None:
            query = query.where(Usuario.activo == activo)
        query = query.order_by(Usuario.username).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_docentes(self, limit: int = 20, offset: int = 0) -> builtins.list[Usuario]:
        query = select(Usuario).where(
            Usuario.rol == RolUsuario.DOCENTE, Usuario.activo
        )
        query = query.order_by(Usuario.username).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, usuario: Usuario, current_user_id: int) -> Usuario:
        usuario.created_by = current_user_id
        usuario.updated_by = current_user_id
        self.db.add(usuario)
        await self.db.flush()
        await self.db.refresh(usuario)
        return usuario

    async def update(self, usuario: Usuario, current_user_id: int) -> Usuario:
        usuario.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(usuario)
        return usuario

    async def soft_delete(self, usuario: Usuario, current_user_id: int) -> Usuario:
        usuario.activo = False
        usuario.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(usuario)
        return usuario

    async def exists_username(self, username: str, exclude_id: int | None = None) -> bool:
        query = select(Usuario.id).where(Usuario.username == username)
        if exclude_id:
            query = query.where(Usuario.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def exists_email(self, email: str, exclude_id: int | None = None) -> bool:
        query = select(Usuario.id).where(Usuario.email == email)
        if exclude_id:
            query = query.where(Usuario.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

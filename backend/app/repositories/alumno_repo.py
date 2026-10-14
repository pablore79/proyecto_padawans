from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alumno import Alumno


class AlumnoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, alumno_id: int) -> Alumno | None:
        result = await self.db.execute(select(Alumno).where(Alumno.id == alumno_id))
        return result.scalar_one_or_none()

    async def get_by_dni(self, dni: str) -> Alumno | None:
        result = await self.db.execute(select(Alumno).where(Alumno.dni == dni))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Alumno | None:
        result = await self.db.execute(select(Alumno).where(Alumno.email == email))
        return result.scalar_one_or_none()

    async def list(
        self,
        activo: bool | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Alumno]:
        query = select(Alumno)
        if activo is not None:
            query = query.where(Alumno.activo == activo)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Alumno.dni.ilike(search_term),
                    Alumno.nombre.ilike(search_term),
                    Alumno.apellido.ilike(search_term),
                )
            )
        query = query.order_by(Alumno.apellido, Alumno.nombre).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        activo: bool | None = None,
        search: str | None = None,
    ) -> int:
        query = select(func.count(Alumno.id))
        if activo is not None:
            query = query.where(Alumno.activo == activo)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Alumno.dni.ilike(search_term),
                    Alumno.nombre.ilike(search_term),
                    Alumno.apellido.ilike(search_term),
                )
            )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, alumno: Alumno, current_user_id: int) -> Alumno:
        alumno.created_by = current_user_id
        alumno.updated_by = current_user_id
        self.db.add(alumno)
        await self.db.flush()
        await self.db.refresh(alumno)
        return alumno

    async def update(self, alumno: Alumno, current_user_id: int) -> Alumno:
        alumno.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(alumno)
        return alumno

    async def soft_delete(self, alumno: Alumno, current_user_id: int) -> Alumno:
        alumno.activo = False
        alumno.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(alumno)
        return alumno

    async def exists_dni(self, dni: str, exclude_id: int | None = None) -> bool:
        query = select(Alumno.id).where(Alumno.dni == dni)
        if exclude_id:
            query = query.where(Alumno.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def exists_email(self, email: str, exclude_id: int | None = None) -> bool:
        query = select(Alumno.id).where(Alumno.email == email)
        if exclude_id:
            query = query.where(Alumno.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

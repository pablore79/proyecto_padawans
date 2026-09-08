
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curso import Curso


class CursoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, curso_id: int) -> Curso | None:
        result = await self.db.execute(select(Curso).where(Curso.id == curso_id))
        return result.scalar_one_or_none()

    async def get_by_nombre(self, nombre: str) -> Curso | None:
        result = await self.db.execute(select(Curso).where(Curso.nombre == nombre))
        return result.scalar_one_or_none()

    async def list(
        self,
        activo: bool | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Curso]:
        query = select(Curso)
        if activo is not None:
            query = query.where(Curso.activo == activo)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Curso.nombre.ilike(search_term),
                    Curso.descripcion.ilike(search_term),
                )
            )
        query = query.order_by(Curso.nombre).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        activo: bool | None = None,
        search: str | None = None,
    ) -> int:
        query = select(func.count(Curso.id))
        if activo is not None:
            query = query.where(Curso.activo == activo)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Curso.nombre.ilike(search_term),
                    Curso.descripcion.ilike(search_term),
                )
            )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, curso: Curso, current_user_id: int) -> Curso:
        curso.created_by = current_user_id
        curso.updated_by = current_user_id
        self.db.add(curso)
        await self.db.flush()
        await self.db.refresh(curso)
        return curso

    async def update(self, curso: Curso, current_user_id: int) -> Curso:
        curso.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(curso)
        return curso

    async def soft_delete(self, curso: Curso, current_user_id: int) -> Curso:
        curso.activo = False
        curso.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(curso)
        return curso

    async def exists_nombre(self, nombre: str, exclude_id: int | None = None) -> bool:
        query = select(Curso.id).where(Curso.nombre == nombre)
        if exclude_id:
            query = query.where(Curso.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_active_inscripciones(self, curso_id: int) -> int:
        from app.models.inscripcion import EstadoInscripcion, Inscripcion

        query = select(func.count(Inscripcion.id)).where(
            Inscripcion.curso_id == curso_id,
            Inscripcion.estado == EstadoInscripcion.ACTIVA,
        )
        result = await self.db.execute(query)
        return result.scalar_one()

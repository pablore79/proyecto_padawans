from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion_docente import AsignacionDocente
from app.models.inscripcion import EstadoInscripcion, Inscripcion


class InscripcionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, inscripcion_id: int) -> Inscripcion | None:
        result = await self.db.execute(select(Inscripcion).where(Inscripcion.id == inscripcion_id))
        return result.scalar_one_or_none()

    async def get_by_alumno_curso(self, alumno_id: int, curso_id: int) -> Inscripcion | None:
        result = await self.db.execute(
            select(Inscripcion).where(
                Inscripcion.alumno_id == alumno_id,
                Inscripcion.curso_id == curso_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_alumno_curso(self, alumno_id: int, curso_id: int) -> Inscripcion | None:
        result = await self.db.execute(
            select(Inscripcion).where(
                Inscripcion.alumno_id == alumno_id,
                Inscripcion.curso_id == curso_id,
                Inscripcion.estado == EstadoInscripcion.ACTIVA,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_curso(
        self,
        curso_id: int,
        estado: EstadoInscripcion | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Inscripcion]:
        query = select(Inscripcion).where(Inscripcion.curso_id == curso_id)
        if estado:
            query = query.where(Inscripcion.estado == estado)
        query = query.order_by(Inscripcion.fecha_inscripcion.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_alumno(
        self,
        alumno_id: int,
        estado: EstadoInscripcion | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Inscripcion]:
        query = select(Inscripcion).where(Inscripcion.alumno_id == alumno_id)
        if estado:
            query = query.where(Inscripcion.estado == estado)
        query = query.order_by(Inscripcion.fecha_inscripcion.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_curso(
        self,
        curso_id: int,
        estado: EstadoInscripcion | None = None,
    ) -> int:
        query = select(func.count(Inscripcion.id)).where(Inscripcion.curso_id == curso_id)
        if estado:
            query = query.where(Inscripcion.estado == estado)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_active_by_curso(self, curso_id: int) -> int:
        query = select(func.count(Inscripcion.id)).where(
            Inscripcion.curso_id == curso_id,
            Inscripcion.estado == EstadoInscripcion.ACTIVA,
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, inscripcion: Inscripcion) -> Inscripcion:
        self.db.add(inscripcion)
        await self.db.flush()
        await self.db.refresh(inscripcion)
        return inscripcion

    async def update(self, inscripcion: Inscripcion) -> Inscripcion:
        await self.db.flush()
        await self.db.refresh(inscripcion)
        return inscripcion

    async def set_baja_by_alumno(self, alumno_id: int) -> int:
        result = await self.db.execute(
            select(Inscripcion).where(
                Inscripcion.alumno_id == alumno_id,
                Inscripcion.estado == EstadoInscripcion.ACTIVA,
            )
        )
        inscripciones = result.scalars().all()
        count = 0
        for inscripcion in inscripciones:
            inscripcion.estado = EstadoInscripcion.BAJA
            count += 1
        await self.db.flush()
        return count

    async def set_baja_by_curso(self, curso_id: int) -> int:
        result = await self.db.execute(
            select(Inscripcion).where(
                Inscripcion.curso_id == curso_id,
                Inscripcion.estado == EstadoInscripcion.ACTIVA,
            )
        )
        inscripciones = result.scalars().all()
        count = 0
        for inscripcion in inscripciones:
            inscripcion.estado = EstadoInscripcion.BAJA
            count += 1
        await self.db.flush()
        return count

    async def get_with_details(
        self, inscripcion_id: int
    ) -> dict[str, str | int | datetime | EstadoInscripcion | None] | None:
        from sqlalchemy.orm import joinedload

        query = (
            select(Inscripcion)
            .options(joinedload(Inscripcion.alumno), joinedload(Inscripcion.curso))
            .where(Inscripcion.id == inscripcion_id)
        )
        result = await self.db.execute(query)
        inscripcion = result.unique().scalar_one_or_none()
        if inscripcion:
            return {
                "id": inscripcion.id,
                "alumno_id": inscripcion.alumno_id,
                "curso_id": inscripcion.curso_id,
                "fecha_inscripcion": inscripcion.fecha_inscripcion,
                "estado": inscripcion.estado,
                "alumno_nombre": inscripcion.alumno.nombre if inscripcion.alumno else None,
                "alumno_apellido": inscripcion.alumno.apellido if inscripcion.alumno else None,
                "alumno_dni": inscripcion.alumno.dni if inscripcion.alumno else None,
                "curso_nombre": inscripcion.curso.nombre if inscripcion.curso else None,
            }
        return None

    async def list_by_curso_with_details(
        self,
        curso_id: int,
        estado: EstadoInscripcion | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, str | int | datetime | EstadoInscripcion | None]]:
        from sqlalchemy.orm import joinedload

        query = (
            select(Inscripcion)
            .options(joinedload(Inscripcion.alumno), joinedload(Inscripcion.curso))
            .where(Inscripcion.curso_id == curso_id)
        )
        if estado:
            query = query.where(Inscripcion.estado == estado)
        query = query.order_by(Inscripcion.fecha_inscripcion.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        inscripciones = result.unique().scalars().all()
        return [
            {
                "id": i.id,
                "alumno_id": i.alumno_id,
                "curso_id": i.curso_id,
                "fecha_inscripcion": i.fecha_inscripcion,
                "estado": i.estado,
                "alumno_nombre": i.alumno.nombre if i.alumno else None,
                "alumno_apellido": i.alumno.apellido if i.alumno else None,
                "alumno_dni": i.alumno.dni if i.alumno else None,
                "curso_nombre": i.curso.nombre if i.curso else None,
            }
            for i in inscripciones
        ]

    async def desasignar_docentes_by_curso(self, curso_id: int) -> int:
        """Delete all docente assignments for a curso. Returns count of deleted assignments."""
        result = await self.db.execute(
            delete(AsignacionDocente).where(AsignacionDocente.curso_id == curso_id)
        )
        return result.rowcount

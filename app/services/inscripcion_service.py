from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.asignacion_docente import AsignacionDocente
from app.models.inscripcion import EstadoInscripcion, Inscripcion
from app.repositories.alumno_repo import AlumnoRepository
from app.repositories.curso_repo import CursoRepository
from app.repositories.inscripcion_repo import InscripcionRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.common import PaginatedResponse
from app.schemas.inscripcion import (
    InscripcionCreate,
    InscripcionListParams,
    InscripcionRead,
)


class InscripcionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inscripcion_repo = InscripcionRepository(db)
        self.alumno_repo = AlumnoRepository(db)
        self.curso_repo = CursoRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    async def create(self, inscripcion_data: InscripcionCreate) -> InscripcionRead:
        alumno = await self.alumno_repo.get(inscripcion_data.alumno_id)
        if not alumno:
            raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")
        if not alumno.activo:
            raise ConflictError("El alumno está dado de baja", "alumno_inactivo")

        curso = await self.curso_repo.get(inscripcion_data.curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")
        if not curso.activo:
            raise ConflictError("El curso está dado de baja", "curso_inactivo")

        active_inscripcion = await self.inscripcion_repo.get_active_by_alumno_curso(
            inscripcion_data.alumno_id, inscripcion_data.curso_id
        )
        if active_inscripcion:
            raise ConflictError(
                "El alumno ya está inscripto activamente en este curso",
                "inscripcion_duplicada",
            )

        active_count = await self.inscripcion_repo.count_active_by_curso(inscripcion_data.curso_id)
        if active_count >= curso.cupos:
            raise ConflictError("El curso ha alcanzado el máximo de cupos", "cupos_completos")

        inscripcion = Inscripcion(
            alumno_id=inscripcion_data.alumno_id,
            curso_id=inscripcion_data.curso_id,
            estado=EstadoInscripcion.ACTIVA,
        )
        created_inscripcion = await self.inscripcion_repo.create(inscripcion)
        details = await self.inscripcion_repo.get_with_details(created_inscripcion.id)
        if not details:
            raise NotFoundError("Inscripción no encontrada", "inscripcion_no_encontrada")
        return InscripcionRead.model_validate(details)

    async def get(self, inscripcion_id: int) -> InscripcionRead:
        result = await self.inscripcion_repo.get_with_details(inscripcion_id)
        if not result:
            raise NotFoundError("Inscripción no encontrada", "inscripcion_no_encontrada")
        return InscripcionRead.model_validate(result)

    async def list_by_curso(
        self, curso_id: int, params: InscripcionListParams
    ) -> PaginatedResponse[InscripcionRead]:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")

        inscripciones = await self.inscripcion_repo.list_by_curso_with_details(
            curso_id=curso_id,
            estado=params.estado,
            limit=params.limit,
            offset=params.offset,
        )
        total = await self.inscripcion_repo.count_by_curso(curso_id, estado=params.estado)
        items = [InscripcionRead.model_validate(i) for i in inscripciones]
        return PaginatedResponse(items=items, total=total, limit=params.limit, offset=params.offset)

    async def list_by_alumno(
        self, alumno_id: int, params: InscripcionListParams
    ) -> PaginatedResponse[InscripcionRead]:
        alumno = await self.alumno_repo.get(alumno_id)
        if not alumno:
            raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")

        inscripciones = await self.inscripcion_repo.list_by_alumno(
            alumno_id=alumno_id,
            estado=params.estado,
            limit=params.limit,
            offset=params.offset,
        )
        total = await self.inscripcion_repo.count_by_curso(alumno_id, estado=params.estado)
        items = [InscripcionRead.model_validate(i) for i in inscripciones]
        return PaginatedResponse(items=items, total=total, limit=params.limit, offset=params.offset)

    async def set_baja(self, curso_id: int, alumno_id: int) -> InscripcionRead:
        inscripcion = await self.inscripcion_repo.get_active_by_alumno_curso(alumno_id, curso_id)
        if not inscripcion:
            raise NotFoundError("Inscripción activa no encontrada", "inscripcion_no_encontrada")

        inscripcion.estado = EstadoInscripcion.BAJA
        updated = await self.inscripcion_repo.update(inscripcion)
        return InscripcionRead.model_validate(
            await self.inscripcion_repo.get_with_details(updated.id)
        )

    async def get_cursos_docente(self, usuario_id: int) -> list[dict[str, Any]]:
        query = select(AsignacionDocente).where(AsignacionDocente.usuario_id == usuario_id)
        result = await self.db.execute(query)
        asignaciones = result.scalars().all()
        cursos = []
        for a in asignaciones:
            curso = await self.curso_repo.get(a.curso_id)
            if curso and curso.activo:
                inscripciones = await self.inscripcion_repo.list_by_curso_with_details(
                    curso_id=curso.id, estado=EstadoInscripcion.ACTIVA
                )
                cursos.append(
                    {
                        "curso": curso,
                        "alumnos": inscripciones,
                    }
                )
        return cursos

    async def get_cursos_alumno(self, alumno_id: int) -> list[dict[str, Any]]:
        inscripciones = await self.inscripcion_repo.list_by_alumno(
            alumno_id=alumno_id, estado=EstadoInscripcion.ACTIVA
        )
        cursos = []
        for i in inscripciones:
            curso = await self.curso_repo.get(i.curso_id)
            if curso and curso.activo:
                cursos.append(
                    {
                        "curso": curso,
                        "inscripcion": i,
                    }
                )
        return cursos

    async def asignar_docente(self, curso_id: int, usuario_id: int) -> dict[str, int]:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")
        if not curso.activo:
            raise ConflictError("El curso está dado de baja", "curso_inactivo")

        usuario = await self.usuario_repo.get(usuario_id)
        if not usuario:
            raise NotFoundError("Usuario no encontrado", "usuario_no_encontrado")
        if not usuario.activo:
            raise ConflictError("El usuario está inactivo", "usuario_inactivo")
        if usuario.rol.value != "docente":
            raise ConflictError("El usuario no tiene rol docente", "usuario_no_es_docente")

        existing = await self.db.execute(
            select(AsignacionDocente).where(
                AsignacionDocente.usuario_id == usuario_id,
                AsignacionDocente.curso_id == curso_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("El docente ya está asignado a este curso", "docente_ya_asignado")

        asignacion = AsignacionDocente(usuario_id=usuario_id, curso_id=curso_id)
        self.db.add(asignacion)
        await self.db.flush()
        return {"curso_id": curso_id, "usuario_id": usuario_id}

    async def desasignar_docente(self, curso_id: int, usuario_id: int) -> None:
        from sqlalchemy import delete

        result = await self.db.execute(
            delete(AsignacionDocente).where(
                AsignacionDocente.usuario_id == usuario_id,
                AsignacionDocente.curso_id == curso_id,
            )
        )
        if result.rowcount == 0:
            raise NotFoundError("Asignación no encontrada", "asignacion_no_encontrada")
        await self.db.flush()

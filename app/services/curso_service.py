from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.curso import Curso
from app.models.materia import Materia
from app.repositories.curso_repo import CursoRepository
from app.repositories.inscripcion_repo import InscripcionRepository
from app.schemas.common import PaginatedResponse
from app.schemas.curso import CursoCreate, CursoRead, CursoUpdate
from app.schemas.materia import MateriaCreate, MateriaRead, MateriaUpdate


class CursoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.curso_repo = CursoRepository(db)
        self.inscripcion_repo = InscripcionRepository(db)

    async def create(self, curso_data: CursoCreate, current_user_id: int) -> CursoRead:
        if await self.curso_repo.exists_nombre(curso_data.nombre):
            raise ConflictError("Ya existe un curso con ese nombre", "curso_duplicado")

        curso = Curso(**curso_data.model_dump())
        created_curso = await self.curso_repo.create(curso, current_user_id)
        return CursoRead.model_validate(created_curso)

    async def get(self, curso_id: int) -> CursoRead:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")
        return CursoRead.model_validate(curso)

    async def list(
        self,
        activo: bool | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResponse[CursoRead]:
        cursos = await self.curso_repo.list(
            activo=activo, search=search, limit=limit, offset=offset
        )
        total = await self.curso_repo.count(activo=activo, search=search)
        items = [CursoRead.model_validate(c) for c in cursos]
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

    async def update(
        self, curso_id: int, curso_data: CursoUpdate, current_user_id: int
    ) -> CursoRead:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")

        update_data = curso_data.model_dump(exclude_unset=True)

        if (
            "nombre" in update_data
            and update_data["nombre"] != curso.nombre
            and await self.curso_repo.exists_nombre(update_data["nombre"], exclude_id=curso_id)
        ):
            raise ConflictError("Ya existe un curso con ese nombre", "curso_duplicado")

        if "cupos" in update_data and update_data["cupos"] is not None:
            active_count = await self.curso_repo.count_active_inscripciones(curso_id)
            if update_data["cupos"] < active_count:
                raise ConflictError(
                    "No se puede reducir cupos por debajo de "
                    f"inscripciones activas ({active_count})",
                    "cupos_insuficientes",
                )

        for field, value in update_data.items():
            setattr(curso, field, value)

        updated_curso = await self.curso_repo.update(curso, current_user_id)
        return CursoRead.model_validate(updated_curso)

    async def soft_delete(self, curso_id: int, current_user_id: int) -> CursoRead:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")

        if not curso.activo:
            raise ConflictError("El curso ya está dado de baja", "curso_ya_inactivo")

        await self.inscripcion_repo.set_baja_by_curso(curso_id)
        deleted_curso = await self.curso_repo.soft_delete(curso, current_user_id)
        return CursoRead.model_validate(deleted_curso)

    async def create_materia(
        self, curso_id: int, materia_data: MateriaCreate, current_user_id: int
    ) -> MateriaRead:
        curso = await self.curso_repo.get(curso_id)
        if not curso:
            raise NotFoundError("Curso no encontrado", "curso_no_encontrado")

        materia = Materia(curso_id=curso_id, **materia_data.model_dump())
        materia.created_by = current_user_id
        materia.updated_by = current_user_id
        self.db.add(materia)
        await self.db.flush()
        await self.db.refresh(materia)
        return MateriaRead.model_validate(materia)

    async def get_materia(self, materia_id: int) -> MateriaRead:
        result = await self.db.execute(select(Materia).where(Materia.id == materia_id))
        materia = result.scalar_one_or_none()
        if not materia:
            raise NotFoundError("Materia no encontrada", "materia_no_encontrada")
        return MateriaRead.model_validate(materia)

    async def list_materias(
        self, curso_id: int, limit: int = 20, offset: int = 0
    ) -> PaginatedResponse[MateriaRead]:
        query = (
            select(Materia)
            .where(Materia.curso_id == curso_id)
            .order_by(Materia.nombre)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        materias = list(result.scalars().all())
        count_query = select(func.count(Materia.id)).where(Materia.curso_id == curso_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        items = [MateriaRead.model_validate(m) for m in materias]
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

    async def update_materia(
        self, materia_id: int, materia_data: MateriaUpdate, current_user_id: int
    ) -> MateriaRead:
        result = await self.db.execute(select(Materia).where(Materia.id == materia_id))
        materia = result.scalar_one_or_none()
        if not materia:
            raise NotFoundError("Materia no encontrada", "materia_no_encontrada")

        update_data = materia_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(materia, field, value)
        materia.updated_by = current_user_id
        await self.db.flush()
        await self.db.refresh(materia)
        return MateriaRead.model_validate(materia)

    async def delete_materia(self, materia_id: int) -> None:
        result = await self.db.execute(select(Materia).where(Materia.id == materia_id))
        materia = result.scalar_one_or_none()
        if not materia:
            raise NotFoundError("Materia no encontrada", "materia_no_encontrada")
        await self.db.delete(materia)
        await self.db.flush()

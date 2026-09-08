
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.alumno import Alumno
from app.repositories.alumno_repo import AlumnoRepository
from app.repositories.inscripcion_repo import InscripcionRepository
from app.schemas.alumno import AlumnoCreate, AlumnoListParams, AlumnoRead, AlumnoUpdate
from app.schemas.common import PaginatedResponse


class AlumnoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alumno_repo = AlumnoRepository(db)
        self.inscripcion_repo = InscripcionRepository(db)

    async def create(self, alumno_data: AlumnoCreate, current_user_id: int) -> AlumnoRead:
        if await self.alumno_repo.exists_dni(alumno_data.dni):
            raise ConflictError("Ya existe un alumno con ese DNI", "dni_duplicado")
        if await self.alumno_repo.exists_email(alumno_data.email):
            raise ConflictError("Ya existe un alumno con ese email", "email_duplicado")

        alumno = Alumno(**alumno_data.model_dump())
        created_alumno = await self.alumno_repo.create(alumno, current_user_id)
        return AlumnoRead.model_validate(created_alumno)

    async def get(self, alumno_id: int) -> AlumnoRead:
        alumno = await self.alumno_repo.get(alumno_id)
        if not alumno:
            raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")
        return AlumnoRead.model_validate(alumno)

    async def list(self, params: AlumnoListParams) -> PaginatedResponse[AlumnoRead]:
        alumnos = await self.alumno_repo.list(
            activo=params.activo,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
        total = await self.alumno_repo.count(activo=params.activo, search=params.search)
        items = [AlumnoRead.model_validate(a) for a in alumnos]
        return PaginatedResponse(
            items=items,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def update(
        self, alumno_id: int, alumno_data: AlumnoUpdate, current_user_id: int
    ) -> AlumnoRead:
        alumno = await self.alumno_repo.get(alumno_id)
        if not alumno:
            raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")

        update_data = alumno_data.model_dump(exclude_unset=True)

        if (
            "dni" in update_data
            and update_data["dni"] != alumno.dni
            and await self.alumno_repo.exists_dni(update_data["dni"], exclude_id=alumno_id)
        ):
            raise ConflictError("Ya existe un alumno con ese DNI", "dni_duplicado")
        if (
            "email" in update_data
            and update_data["email"] != alumno.email
            and await self.alumno_repo.exists_email(update_data["email"], exclude_id=alumno_id)
        ):
            raise ConflictError("Ya existe un alumno con ese email", "email_duplicado")

        for field, value in update_data.items():
            setattr(alumno, field, value)

        updated_alumno = await self.alumno_repo.update(alumno, current_user_id)
        return AlumnoRead.model_validate(updated_alumno)

    async def soft_delete(self, alumno_id: int, current_user_id: int) -> AlumnoRead:
        alumno = await self.alumno_repo.get(alumno_id)
        if not alumno:
            raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")

        if not alumno.activo:
            raise ConflictError("El alumno ya está dado de baja", "alumno_ya_inactivo")

        await self.inscripcion_repo.set_baja_by_alumno(alumno_id)
        deleted_alumno = await self.alumno_repo.soft_delete(alumno, current_user_id)
        return AlumnoRead.model_validate(deleted_alumno)

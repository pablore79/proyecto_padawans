from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.alumno import AlumnoCreate, AlumnoListParams, AlumnoRead, AlumnoUpdate
from app.schemas.common import PaginatedResponse
from app.services.alumno_service import AlumnoService

router = APIRouter(prefix="/alumnos", tags=["Alumnos"])


@router.get("", response_model=PaginatedResponse[AlumnoRead])
async def list_alumnos(
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(None, description="Buscar por DNI, nombre o apellido"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AlumnoRead]:
    service = AlumnoService(db)
    params = AlumnoListParams(activo=activo, search=search, limit=limit, offset=offset)
    return await service.list(params)


@router.post("", response_model=AlumnoRead, status_code=201)
async def create_alumno(
    alumno_data: AlumnoCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AlumnoRead:
    service = AlumnoService(db)
    return await service.create(alumno_data, current_user.id)


@router.get("/{alumno_id}", response_model=AlumnoRead)
async def get_alumno(
    alumno_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AlumnoRead:
    service = AlumnoService(db)
    return await service.get(alumno_id)


@router.patch("/{alumno_id}", response_model=AlumnoRead)
async def update_alumno(
    alumno_id: int,
    alumno_data: AlumnoUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AlumnoRead:
    service = AlumnoService(db)
    return await service.update(alumno_id, alumno_data, current_user.id)


@router.delete("/{alumno_id}", response_model=AlumnoRead)
async def delete_alumno(
    alumno_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AlumnoRead:
    service = AlumnoService(db)
    return await service.soft_delete(alumno_id, current_user.id)


@router.post("/{alumno_id}/reactivar", response_model=AlumnoRead)
async def reactivar_alumno(
    alumno_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AlumnoRead:
    service = AlumnoService(db)
    alumno = await service.alumno_repo.get(alumno_id)
    if not alumno:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Alumno no encontrado", "alumno_no_encontrado")
    if alumno.activo:
        from app.core.exceptions import ConflictError

        raise ConflictError("El alumno ya está activo", "alumno_ya_activo")
    alumno.activo = True
    alumno.updated_by = current_user.id
    await service.db.flush()
    await service.db.refresh(alumno)
    return AlumnoRead.model_validate(alumno)

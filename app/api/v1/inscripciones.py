from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.inscripcion import (
    InscripcionCreate,
    InscripcionListParams,
    InscripcionRead,
)
from app.services.inscripcion_service import InscripcionService

router = APIRouter(prefix="/cursos/{curso_id}/inscripciones", tags=["Inscripciones"])


@router.post("", response_model=InscripcionRead, status_code=201)
async def create_inscripcion(
    curso_id: int,
    inscripcion_data: InscripcionCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = InscripcionService(db)
    if inscripcion_data.curso_id != curso_id:
        from app.core.exceptions import ValidationError

        raise ValidationError(
            "El curso_id del body debe coincidir con el de la URL", "validacion_error"
        )
    return await service.create(inscripcion_data)


@router.get("", response_model=PaginatedResponse[InscripcionRead])
async def list_inscripciones(
    curso_id: int,
    estado: str | None = Query(None, description="Filtrar por estado (activa, baja)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.inscripcion import EstadoInscripcion

    service = InscripcionService(db)
    params = InscripcionListParams(
        estado=EstadoInscripcion(estado) if estado else None,
        limit=limit,
        offset=offset,
    )
    return await service.list_by_curso(curso_id, params)


@router.delete("/{alumno_id}", response_model=InscripcionRead)
async def delete_inscripcion(
    curso_id: int,
    alumno_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = InscripcionService(db)
    return await service.set_baja(curso_id, alumno_id)

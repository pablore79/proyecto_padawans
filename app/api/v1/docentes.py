from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse
from app.services.inscripcion_service import InscripcionService

router = APIRouter(prefix="/cursos/{curso_id}/docentes", tags=["Asignación Docente"])


@router.post("", response_model=dict, status_code=201)
async def asignar_docente(
    curso_id: int,
    usuario_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = InscripcionService(db)
    return await service.asignar_docente(curso_id, usuario_id)


@router.delete("/{usuario_id}", response_model=MessageResponse)
async def desasignar_docente(
    curso_id: int,
    usuario_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = InscripcionService(db)
    await service.desasignar_docente(curso_id, usuario_id)
    return MessageResponse(message="Docente desasignado correctamente", code="docente_desasignado")

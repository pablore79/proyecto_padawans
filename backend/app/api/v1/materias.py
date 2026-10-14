from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.materia import MateriaCreate, MateriaRead, MateriaUpdate
from app.services.curso_service import CursoService

router = APIRouter(prefix="/cursos/{curso_id}/materias", tags=["Materias"])


@router.post("", response_model=MateriaRead, status_code=201)
async def create_materia(
    curso_id: int,
    materia_data: MateriaCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    return await service.create_materia(curso_id, materia_data, current_user.id)


@router.get("", response_model=PaginatedResponse[MateriaRead])
async def list_materias(
    curso_id: int,
    limit: int = 20,
    offset: int = 0,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[MateriaRead]:
    service = CursoService(db)
    return await service.list_materias(curso_id, limit, offset)


@router.get("/{materia_id}", response_model=MateriaRead)
async def get_materia(
    curso_id: int,
    materia_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    return await service.get_materia(materia_id)


@router.patch("/{materia_id}", response_model=MateriaRead)
async def update_materia(
    curso_id: int,
    materia_id: int,
    materia_data: MateriaUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    return await service.update_materia(materia_id, materia_data, current_user.id)


@router.delete("/{materia_id}", response_model=MateriaRead)
async def delete_materia(
    curso_id: int,
    materia_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    materia = await service.get_materia(materia_id)
    await service.delete_materia(materia_id)
    return materia

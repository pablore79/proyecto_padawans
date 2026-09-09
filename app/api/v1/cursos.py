from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.curso import CursoCreate, CursoRead, CursoUpdate
from app.schemas.materia import MateriaCreate, MateriaRead, MateriaUpdate
from app.services.curso_service import CursoService

router = APIRouter(prefix="/cursos", tags=["Cursos"])


@router.get("", response_model=PaginatedResponse[CursoRead])
async def list_cursos(
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(None, description="Buscar por nombre o descripción"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CursoRead]:
    service = CursoService(db)
    return await service.list(activo=activo, search=search, limit=limit, offset=offset)


@router.post("", response_model=CursoRead, status_code=201)
async def create_curso(
    curso_data: CursoCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CursoRead:
    service = CursoService(db)
    return await service.create(curso_data, current_user.id)


@router.get("/{curso_id}", response_model=CursoRead)
async def get_curso(
    curso_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CursoRead:
    service = CursoService(db)
    return await service.get(curso_id)


@router.patch("/{curso_id}", response_model=CursoRead)
async def update_curso(
    curso_id: int,
    curso_data: CursoUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CursoRead:
    service = CursoService(db)
    return await service.update(curso_id, curso_data, current_user.id)


@router.delete("/{curso_id}", response_model=CursoRead)
async def delete_curso(
    curso_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CursoRead:
    service = CursoService(db)
    return await service.soft_delete(curso_id, current_user.id)


@router.post("/{curso_id}/reactivar", response_model=CursoRead)
async def reactivar_curso(
    curso_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CursoRead:
    service = CursoService(db)
    curso = await service.curso_repo.get(curso_id)
    if not curso:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Curso no encontrado", "curso_no_encontrado")
    if curso.activo:
        from app.core.exceptions import ConflictError

        raise ConflictError("El curso ya está activo", "curso_ya_activo")
    curso.activo = True
    curso.updated_by = current_user.id
    await service.db.flush()
    await service.db.refresh(curso)
    return CursoRead.model_validate(curso)


@router.get("/{curso_id}/materias", response_model=PaginatedResponse[MateriaRead])
async def list_materias(
    curso_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[MateriaRead]:
    service = CursoService(db)
    return await service.list_materias(curso_id, limit, offset)


@router.post("/{curso_id}/materias", response_model=MateriaRead, status_code=201)
async def create_materia(
    curso_id: int,
    materia_data: MateriaCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    return await service.create_materia(curso_id, materia_data, current_user.id)


@router.patch("/materias/{materia_id}", response_model=MateriaRead)
async def update_materia(
    materia_id: int,
    materia_data: MateriaUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MateriaRead:
    service = CursoService(db)
    return await service.update_materia(materia_id, materia_data, current_user.id)


@router.delete("/materias/{materia_id}", status_code=204)
async def delete_materia(
    materia_id: int,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = CursoService(db)
    await service.delete_materia(materia_id)
    return None

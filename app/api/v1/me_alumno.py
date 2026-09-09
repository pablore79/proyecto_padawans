from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_alumno
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.inscripcion_service import InscripcionService

router = APIRouter(prefix="/alumno/me", tags=["Alumno - Mis Cursos"])


@router.get("/cursos")
async def mis_cursos(
    current_user: Usuario = Depends(require_alumno),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if not current_user.alumno_id:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError("Usuario alumno sin alumno_id asociado", "rol_alumno_sin_alumno_id")

    service = InscripcionService(db)
    cursos = await service.get_cursos_alumno(current_user.alumno_id)
    return {
        "alumno_id": current_user.alumno_id,
        "alumno_username": current_user.username,
        "cursos": [
            {
                "id": c["curso"].id,
                "nombre": c["curso"].nombre,
                "descripcion": c["curso"].descripcion,
                "cupos": c["curso"].cupos,
                "fecha_inscripcion": c["inscripcion"].fecha_inscripcion,
            }
            for c in cursos
        ],
    }

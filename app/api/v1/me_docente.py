from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_docente
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.inscripcion_service import InscripcionService

router = APIRouter(prefix="/docente/me", tags=["Docente - Mis Cursos"])


@router.get("/cursos")
async def mis_cursos(
    current_user: Usuario = Depends(require_docente),
    db: AsyncSession = Depends(get_db),
):
    service = InscripcionService(db)
    cursos = await service.get_cursos_docente(current_user.id)
    return {
        "docente_id": current_user.id,
        "docente_username": current_user.username,
        "cursos": [
            {
                "id": c["curso"].id,
                "nombre": c["curso"].nombre,
                "descripcion": c["curso"].descripcion,
                "cupos": c["curso"].cupos,
                "alumnos": [
                    {
                        "id": a["alumno_id"],
                        "nombre": a["alumno_nombre"],
                        "apellido": a["alumno_apellido"],
                        "dni": a["alumno_dni"],
                        "fecha_inscripcion": a["fecha_inscripcion"],
                    }
                    for a in c["alumnos"]
                ],
            }
            for c in cursos
        ],
    }

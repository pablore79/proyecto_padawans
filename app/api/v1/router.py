from fastapi import APIRouter

from app.api.v1 import (
    alumnos,
    auth,
    cursos,
    docentes,
    inscripciones,
    materias,
    me_alumno,
    me_docente,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(alumnos.router)
router.include_router(cursos.router)
router.include_router(materias.router)
router.include_router(inscripciones.router)
router.include_router(docentes.router)
router.include_router(me_docente.router)
router.include_router(me_alumno.router)

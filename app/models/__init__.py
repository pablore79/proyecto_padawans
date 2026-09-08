from app.core.database import Base
from app.models.alumno import Alumno
from app.models.asignacion_docente import AsignacionDocente
from app.models.curso import Curso
from app.models.inscripcion import EstadoInscripcion, Inscripcion
from app.models.materia import Materia
from app.models.usuario import RolUsuario, Usuario

__all__ = [
    "Base",
    "Alumno",
    "Curso",
    "Materia",
    "Inscripcion",
    "EstadoInscripcion",
    "AsignacionDocente",
    "Usuario",
    "RolUsuario",
]

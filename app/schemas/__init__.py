from app.schemas.alumno import AlumnoBase, AlumnoCreate, AlumnoListParams, AlumnoRead, AlumnoUpdate
from app.schemas.auth import LoginRequest, Token, TokenData, UserBase, UserCreate, UserRead
from app.schemas.common import ErrorResponse, MessageResponse, PaginatedResponse, PaginationParams
from app.schemas.curso import CursoBase, CursoCreate, CursoRead, CursoUpdate
from app.schemas.inscripcion import (
    InscripcionBase,
    InscripcionCreate,
    InscripcionEstadoUpdate,
    InscripcionListParams,
    InscripcionRead,
)
from app.schemas.materia import MateriaBase, MateriaCreate, MateriaRead, MateriaUpdate

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "MessageResponse",
    "UserBase",
    "UserCreate",
    "UserRead",
    "LoginRequest",
    "Token",
    "TokenData",
    "AlumnoBase",
    "AlumnoCreate",
    "AlumnoUpdate",
    "AlumnoRead",
    "AlumnoListParams",
    "CursoBase",
    "CursoCreate",
    "CursoUpdate",
    "CursoRead",
    "MateriaBase",
    "MateriaCreate",
    "MateriaUpdate",
    "MateriaRead",
    "InscripcionBase",
    "InscripcionCreate",
    "InscripcionRead",
    "InscripcionEstadoUpdate",
    "InscripcionListParams",
]

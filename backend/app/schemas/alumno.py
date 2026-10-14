from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AlumnoBase(BaseModel):
    dni: str = Field(..., min_length=7, max_length=20, pattern=r"^\d{7,8}[A-Z]?$")
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    telefono: str | None = Field(None, max_length=30)
    fecha_nacimiento: date | None = None
    usuario_github: str | None = Field(None, max_length=100)
    usuario_gitlab: str | None = Field(None, max_length=100)
    perfil_linkedin: str | None = Field(None, max_length=255)


class AlumnoCreate(AlumnoBase):
    pass


class AlumnoUpdate(BaseModel):
    dni: str | None = Field(None, min_length=7, max_length=20, pattern=r"^\d{7,8}[A-Z]?$")
    nombre: str | None = Field(None, min_length=1, max_length=100)
    apellido: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    fecha_nacimiento: date | None = None
    usuario_github: str | None = Field(None, max_length=100)
    usuario_gitlab: str | None = Field(None, max_length=100)
    perfil_linkedin: str | None = Field(None, max_length=255)
    activo: bool | None = None


class AlumnoRead(AlumnoBase):
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    updated_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class AlumnoListParams(BaseModel):
    activo: bool | None = None
    search: str | None = Field(None, description="Búsqueda por DNI, nombre o apellido")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

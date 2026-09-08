from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CursoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=500)
    cupos: int = Field(default=20, ge=1, le=500)


class CursoCreate(CursoBase):
    pass


class CursoUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=500)
    cupos: int | None = Field(None, ge=1, le=500)
    activo: bool | None = None


class CursoRead(CursoBase):
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    updated_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

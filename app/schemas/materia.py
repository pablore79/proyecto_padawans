from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MateriaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=500)


class MateriaCreate(MateriaBase):
    pass


class MateriaUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=500)


class MateriaRead(MateriaBase):
    id: int
    curso_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

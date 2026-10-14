from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.inscripcion import EstadoInscripcion


class InscripcionBase(BaseModel):
    alumno_id: int = Field(..., gt=0)
    curso_id: int = Field(..., gt=0)


class InscripcionCreate(InscripcionBase):
    pass


class InscripcionRead(InscripcionBase):
    id: int
    fecha_inscripcion: datetime
    estado: EstadoInscripcion
    alumno_nombre: str | None = None
    alumno_apellido: str | None = None
    alumno_dni: str | None = None
    curso_nombre: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("estado")
    def serialize_estado(self, value: EstadoInscripcion) -> str:
        return value.name


class InscripcionEstadoUpdate(BaseModel):
    estado: EstadoInscripcion


class InscripcionListParams(BaseModel):
    estado: EstadoInscripcion | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

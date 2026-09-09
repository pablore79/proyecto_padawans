from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.alumno import Alumno
    from app.models.curso import Curso


class EstadoInscripcion(str, PyEnum):
    ACTIVA = "activa"
    BAJA = "baja"


class Inscripcion(Base, TimestampMixin):
    __tablename__ = "inscripciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alumno_id: Mapped[int] = mapped_column(
        ForeignKey("alumnos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_inscripcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    estado: Mapped[EstadoInscripcion] = mapped_column(
        Enum(EstadoInscripcion, native_enum=False, length=10),
        default=EstadoInscripcion.ACTIVA,
        nullable=False,
    )

    alumno: Mapped["Alumno"] = relationship(
        "Alumno", back_populates="inscripciones", lazy="selectin"
    )
    curso: Mapped["Curso"] = relationship("Curso", back_populates="inscripciones", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("alumno_id", "curso_id", name="uq_inscripciones_alumno_curso"),
        # Partial unique index for active inscriptions only
        Index(
            "ix_inscripciones_alumno_curso_activa",
            "alumno_id",
            "curso_id",
            unique=True,
            postgresql_where=text("estado = 'activa'"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Inscripcion(id={self.id}, alumno_id={self.alumno_id}, "
            f"curso_id={self.curso_id}, estado='{self.estado}')>"
        )

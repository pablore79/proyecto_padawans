from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.asignacion_docente import AsignacionDocente
    from app.models.inscripcion import Inscripcion
    from app.models.materia import Materia


class Curso(Base, TimestampMixin, AuditMixin):
    __tablename__ = "cursos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cupos: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    materias: Mapped[list["Materia"]] = relationship(
        "Materia", back_populates="curso", lazy="selectin", cascade="all, delete-orphan"
    )
    inscripciones: Mapped[list["Inscripcion"]] = relationship(
        "Inscripcion", back_populates="curso", lazy="selectin"
    )
    asignaciones_docente: Mapped[list["AsignacionDocente"]] = relationship(
        "AsignacionDocente", back_populates="curso", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("nombre", name="uq_cursos_nombre"),)

    def __repr__(self) -> str:
        return (
            f"<Curso(id={self.id}, nombre='{self.nombre}', "
            f"cupos={self.cupos}, activo={self.activo})>"
        )

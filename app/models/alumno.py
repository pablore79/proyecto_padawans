from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion
    from app.models.usuario import Usuario


class Alumno(Base, TimestampMixin, AuditMixin):
    __tablename__ = "alumnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario_github: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usuario_gitlab: Mapped[str | None] = mapped_column(String(100), nullable=True)
    perfil_linkedin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inscripciones: Mapped[list["Inscripcion"]] = relationship(
        "Inscripcion", back_populates="alumno", lazy="selectin"
    )
    usuario: Mapped["Usuario | None"] = relationship(
        "Usuario", back_populates="alumno", lazy="selectin", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("dni", name="uq_alumnos_dni"),
        UniqueConstraint("email", name="uq_alumnos_email"),
    )

    def __repr__(self) -> str:
        return (
            f"<Alumno(id={self.id}, dni='{self.dni}', nombre='{self.nombre}', "
            f"apellido='{self.apellido}')>"
        )

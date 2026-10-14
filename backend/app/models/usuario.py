from __future__ import annotations

from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.alumno import Alumno
    from app.models.asignacion_docente import AsignacionDocente


class RolUsuario(str, PyEnum):
    ADMIN = "admin"
    DOCENTE = "docente"
    ALUMNO = "alumno"


class Usuario(Base, TimestampMixin, AuditMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, native_enum=False, length=10), nullable=False
    )
    alumno_id: Mapped[int | None] = mapped_column(
        ForeignKey("alumnos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    alumno: Mapped["Alumno | None"] = relationship(
        "Alumno", back_populates="usuario", lazy="selectin"
    )
    asignaciones_docente: Mapped[list["AsignacionDocente"]] = relationship(
        "AsignacionDocente", back_populates="usuario", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("username", name="uq_usuarios_username"),
        UniqueConstraint("email", name="uq_usuarios_email"),
    )

    def __repr__(self) -> str:
        return (
            f"<Usuario(id={self.id}, username='{self.username}', "
            f"rol='{self.rol}', alumno_id={self.alumno_id})>"
        )

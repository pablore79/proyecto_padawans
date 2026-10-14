from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.curso import Curso


class Materia(Base, TimestampMixin, AuditMixin):
    __tablename__ = "materias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    curso: Mapped["Curso"] = relationship("Curso", back_populates="materias", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Materia(id={self.id}, curso_id={self.curso_id}, nombre='{self.nombre}')>"

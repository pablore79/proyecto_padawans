
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AsignacionDocente(Base, TimestampMixin):
    __tablename__ = "asignaciones_docente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="asignaciones_docente", lazy="selectin"
    )
    curso: Mapped["Curso"] = relationship(
        "Curso", back_populates="asignaciones_docente", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("usuario_id", "curso_id", name="uq_asignacion_docente_usuario_curso"),
    )

    def __repr__(self) -> str:
        return f"<AsignacionDocente(id={self.id}, usuario_id={self.usuario_id}, curso_id={self.curso_id})>"

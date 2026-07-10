"""Model de subcategoria, filha de uma categoria."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Subcategoria(Base):
    """Subcategoria de uma categoria (ex: ALIMENTACAO -> Delivery)."""

    __tablename__ = "subcategorias"
    __table_args__ = (UniqueConstraint("categoria_id", "nome", name="uq_subcategoria_categoria_nome"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    categoria: Mapped["Categoria"] = relationship(  # noqa: F821
        "Categoria", back_populates="subcategorias"
    )

    def __repr__(self) -> str:
        return f"<Subcategoria id={self.id} nome={self.nome!r} categoria_id={self.categoria_id}>"

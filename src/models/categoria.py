"""Model de categoria (taxonomia de despesas e receitas)."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Categoria(Base):
    """Categoria de despesa ou receita (ex: ALIMENTACAO, SALARIO FRED)."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    cor: Mapped[str] = mapped_column(String(7), nullable=False, default="#888780")
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="despesa")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subcategorias: Mapped[list["Subcategoria"]] = relationship(  # noqa: F821
        "Subcategoria", back_populates="categoria", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Categoria id={self.id} nome={self.nome!r} tipo={self.tipo!r}>"

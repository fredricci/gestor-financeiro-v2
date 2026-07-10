"""Model de regra de categorização aprendida a partir de correções do usuário."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Regra(Base):
    """Regra descrição -> categoria/subcategoria (chave normalizada em maiúsculas)."""

    __tablename__ = "regras"

    descricao: Mapped[str] = mapped_column(Text, primary_key=True)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Regra descricao={self.descricao!r} categoria={self.categoria!r}>"

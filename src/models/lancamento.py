"""Model de lançamento financeiro (a transação em si)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Lancamento(Base):
    """Lançamento importado de CSV/OFX/imagem ou lançado manualmente."""

    __tablename__ = "lancamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tipo_valor: Mapped[str] = mapped_column(String(10), nullable=False, default="saida")
    categoria: Mapped[str] = mapped_column(String(80), nullable=False, default="NAO LEMBRO")
    subcategoria: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    origem: Mapped[str] = mapped_column(String(20), nullable=False, default="ia")
    confianca: Mapped[str] = mapped_column(String(10), nullable=False, default="baixa")
    confirmado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    arquivo: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    fitid: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Lancamento id={self.id} data={self.data} descricao={self.descricao!r} valor={self.valor}>"

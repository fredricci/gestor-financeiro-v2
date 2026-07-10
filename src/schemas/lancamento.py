"""Schemas de Lançamento."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

TipoValor = Literal["entrada", "saida"]
Origem = Literal["regra_usuario", "ia", "confirmado", "manual", "erro"]
Confianca = Literal["alta", "media", "baixa"]


class LancamentoCreate(BaseModel):
    data: date
    descricao: str = Field(min_length=1)
    valor: Decimal = Field(gt=0, description="Valor sempre positivo (o sinal vem de tipo_valor)")
    tipo_valor: TipoValor = "saida"
    categoria: str = "NAO LEMBRO"
    subcategoria: str = ""
    origem: Origem = "manual"
    confianca: Confianca = "alta"
    confirmado: bool = True
    arquivo: str = "manual"
    fitid: str = ""


class LancamentoUpdate(BaseModel):
    """Atualização parcial — todos os campos são opcionais."""

    data: date | None = None
    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0)
    tipo_valor: TipoValor | None = None
    categoria: str | None = None
    subcategoria: str | None = None
    confirmado: bool | None = None


class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    descricao: str
    valor: Decimal
    tipo_valor: str
    categoria: str
    subcategoria: str
    origem: str
    confianca: str
    confirmado: bool
    arquivo: str
    fitid: str
    criado_em: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fonte(self) -> str:
        """Deriva a fonte do lançamento a partir do nome do arquivo."""
        arq = (self.arquivo or "").lower()
        if arq.endswith(".ofx"):
            return "extrato"
        if arq == "manual" or arq == "":
            return "manual"
        return "fatura"


class IdList(BaseModel):
    ids: list[int] = Field(min_length=1)

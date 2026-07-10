"""Schemas do endpoint de categorização (sugestão sem persistência)."""

from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.lancamento import TipoValor


class CategorizarItem(BaseModel):
    descricao: str = Field(min_length=1)
    valor: Decimal | None = None
    tipo_valor: TipoValor = "saida"


class CategorizarRequest(BaseModel):
    lancamentos: list[CategorizarItem] = Field(min_length=1)


class CategorizarResultado(BaseModel):
    descricao: str
    categoria: str
    subcategoria: str
    confianca: str
    origem: str
    tipo_valor: str

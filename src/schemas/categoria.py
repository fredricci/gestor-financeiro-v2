"""Schemas de Categoria e Subcategoria."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Tipo = Literal["despesa", "receita"]


class SubcategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class SubcategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)

    @field_validator("nome")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class SubcategoriaUpdate(SubcategoriaCreate):
    pass


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    cor: str = Field(default="#888780", max_length=7)
    tipo: Tipo = "despesa"

    @field_validator("nome")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class CategoriaUpdate(CategoriaCreate):
    pass


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cor: str
    tipo: str
    criado_em: datetime
    subcategorias: list[SubcategoriaOut] = []

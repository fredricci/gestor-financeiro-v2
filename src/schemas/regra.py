"""Schemas de Regra de categorização."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegraUpsert(BaseModel):
    descricao: str = Field(min_length=1)
    categoria: str = Field(min_length=1)
    subcategoria: str = ""

    @field_validator("descricao")
    @classmethod
    def _norm(cls, v: str) -> str:
        return v.strip().upper()


class RegraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    descricao: str
    categoria: str
    subcategoria: str


class RegrasBatch(BaseModel):
    regras: list[RegraUpsert] = Field(min_length=1)

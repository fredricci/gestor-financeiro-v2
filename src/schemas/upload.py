"""Schemas de resposta do upload de arquivos."""

from pydantic import BaseModel

from src.schemas.lancamento import LancamentoOut


class UploadResumo(BaseModel):
    arquivo: str
    total_lidos: int
    novos: int
    duplicados: int
    por_origem: dict[str, int]
    lancamentos: list[LancamentoOut]

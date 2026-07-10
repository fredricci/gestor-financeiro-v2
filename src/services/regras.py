"""Persistência de regras de categorização (upsert idempotente)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Regra
from src.services.normalizacao import normalizar


async def upsert_regra(
    session: AsyncSession, descricao: str, categoria: str, subcategoria: str = ""
) -> Regra:
    """Cria ou atualiza uma regra por descrição normalizada. Não faz commit."""
    chave = normalizar(descricao)
    regra = (
        await session.execute(select(Regra).where(Regra.descricao == chave))
    ).scalar_one_or_none()
    if regra:
        regra.categoria = categoria
        regra.subcategoria = subcategoria or ""
    else:
        regra = Regra(descricao=chave, categoria=categoria, subcategoria=subcategoria or "")
        session.add(regra)
    return regra

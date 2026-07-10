"""Serviço de categorização: casa regras do usuário e delega o resto à IA."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Regra
from src.services.claude_client import Categorizer
from src.services.normalizacao import chave_regra

# Máximo de regras enviadas como histórico no prompt da IA.
LIMITE_HISTORICO = 200


async def buscar_regra(session: AsyncSession, descricao: str) -> Regra | None:
    """Procura uma regra por match exato e, se falhar, por substring.

    O substring casa quando a chave da regra (>= 5 caracteres) está contida
    na descrição normalizada — evita falsos positivos com chaves curtas.
    """
    chave = chave_regra(descricao)

    exata = (
        await session.execute(select(Regra).where(Regra.descricao == chave))
    ).scalar_one_or_none()
    if exata:
        return exata

    regras = (await session.execute(select(Regra))).scalars().all()
    for regra in regras:
        if len(regra.descricao) >= 5 and regra.descricao in chave:
            return regra
    return None


async def _carregar_historico(session: AsyncSession) -> list[tuple[str, str, str]]:
    rows = (
        await session.execute(
            select(Regra.descricao, Regra.categoria, Regra.subcategoria)
            .order_by(Regra.descricao)
            .limit(LIMITE_HISTORICO)
        )
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


async def sugerir_categorias(
    session: AsyncSession,
    itens: list[dict],
    categorizer: Categorizer,
) -> list[dict]:
    """Retorna uma sugestão de categoria para cada item (mesma ordem).

    Cada item deve ter 'descricao' e, opcionalmente, 'valor' e 'tipo_valor'.
    Não persiste nada — apenas sugere.
    """
    resultado: list[dict | None] = [None] * len(itens)
    para_ia: list[dict] = []
    indices_ia: list[int] = []

    for i, item in enumerate(itens):
        regra = await buscar_regra(session, item["descricao"])
        if regra:
            resultado[i] = {
                "descricao": item["descricao"],
                "categoria": regra.categoria,
                "subcategoria": regra.subcategoria,
                "confianca": "alta",
                "origem": "regra_usuario",
                "tipo_valor": item.get("tipo_valor", "saida"),
            }
        else:
            para_ia.append(item)
            indices_ia.append(i)

    if para_ia:
        historico = await _carregar_historico(session)
        respostas = await categorizer.categorizar(para_ia, historico)
        for idx, resposta in zip(indices_ia, respostas, strict=True):
            resultado[idx] = resposta

    return [r for r in resultado if r is not None]

"""Consultas e transformações para as telas (camada de apresentação)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Categoria, Lancamento
from src.templating import format_brl


def _fonte_de_arquivo(arquivo: str) -> str:
    arq = (arquivo or "").lower()
    if arq.endswith(".ofx"):
        return "extrato"
    if arq == "manual" or arq == "":
        return "manual"
    return "fatura"


def lancamento_to_dict(lanc: Lancamento) -> dict:
    """Serializa um Lancamento para dict de apresentação (valor float, data ISO, fonte)."""
    return {
        "id": lanc.id,
        "data": lanc.data.isoformat(),
        "descricao": lanc.descricao,
        "valor": float(lanc.valor),
        "tipo_valor": lanc.tipo_valor,
        "categoria": lanc.categoria,
        "subcategoria": lanc.subcategoria or "",
        "origem": lanc.origem,
        "confianca": lanc.confianca,
        "confirmado": lanc.confirmado,
        "arquivo": lanc.arquivo,
        "fitid": lanc.fitid,
        "fonte": _fonte_de_arquivo(lanc.arquivo),
    }


async def fetch_lancamentos(session: AsyncSession) -> list[dict]:
    """Todos os lançamentos como dicts (inclui 'fonte' derivada)."""
    rows = (
        await session.execute(
            select(Lancamento).order_by(Lancamento.data.desc(), Lancamento.id.desc())
        )
    ).scalars().all()
    return [lancamento_to_dict(r) for r in rows]


async def fetch_categorias(session: AsyncSession) -> list[dict]:
    """Categorias com subcategorias aninhadas, ordenadas por tipo e nome."""
    cats = (
        await session.execute(
            select(Categoria)
            .options(selectinload(Categoria.subcategorias))
            .order_by(Categoria.tipo, Categoria.nome)
        )
    ).scalars().all()
    return [
        {
            "id": c.id,
            "nome": c.nome,
            "cor": c.cor,
            "tipo": c.tipo,
            "subcategorias": [{"id": s.id, "nome": s.nome} for s in c.subcategorias],
        }
        for c in cats
    ]


async def compute_metricas(session: AsyncSession) -> dict:
    """Métricas globais exibidas no topo do upload."""
    total = (await session.execute(select(func.count()).select_from(Lancamento))).scalar_one()
    hist = (
        await session.execute(
            select(func.count())
            .select_from(Lancamento)
            .where(Lancamento.origem.in_(("regra_usuario", "confirmado")))
        )
    ).scalar_one()
    ia = (
        await session.execute(
            select(func.count()).select_from(Lancamento).where(Lancamento.origem == "ia")
        )
    ).scalar_one()
    saidas = (
        await session.execute(
            select(func.coalesce(func.sum(Lancamento.valor), 0)).where(
                Lancamento.tipo_valor == "saida"
            )
        )
    ).scalar_one()
    return {
        "total": total,
        "historico": hist,
        "ia": ia,
        "total_saidas": float(saidas or 0),
    }


def _fonte(lanc: dict) -> str:
    return lanc.get("fonte", "")


def filtrar_ordenar(lancamentos: list[dict], filtros: dict) -> list[dict]:
    """Aplica filtros da UI (origem/fonte/mês/busca) e ordenação. Função pura."""
    origem = filtros.get("origem", "todos")
    fonte = filtros.get("fonte", "todos")
    mes = filtros.get("mes", "todos")
    busca = (filtros.get("busca") or "").lower().strip()
    ordem = filtros.get("ordem", "data")
    direcao = filtros.get("direcao", "desc")

    lista = list(lancamentos)

    if origem == "historico":
        lista = [x for x in lista if x["origem"] in ("regra_usuario", "confirmado")]
    elif origem == "alta":
        lista = [x for x in lista if x["confianca"] == "alta" and x["origem"] == "ia"]
    elif origem == "media":
        lista = [x for x in lista if x["confianca"] == "media"]
    elif origem == "baixa":
        lista = [x for x in lista if x["confianca"] == "baixa"]

    if fonte != "todos":
        lista = [x for x in lista if _fonte(x) == fonte]

    if mes != "todos":
        lista = [x for x in lista if str(x["data"])[:7] == mes]

    if busca:
        def casa(x: dict) -> bool:
            valor_fmt = format_brl(x["valor"]).lower()
            return (
                busca in x["descricao"].lower()
                or busca in x["categoria"].lower()
                or busca in (x.get("subcategoria") or "").lower()
                or busca in str(x["valor"])
                or busca in valor_fmt
            )

        lista = [x for x in lista if casa(x)]

    reverse = direcao == "desc"

    def chave(x: dict):
        if ordem == "valor":
            return x["valor"]
        if ordem == "categoria":
            return (x["categoria"] + (x.get("subcategoria") or "")).lower()
        return str(x["data"])

    lista.sort(key=chave, reverse=reverse)
    return lista


def meses_disponiveis(lancamentos: list[dict]) -> list[str]:
    """Meses 'YYYY-MM' presentes, mais recentes primeiro."""
    return sorted({str(x["data"])[:7] for x in lancamentos}, reverse=True)


def build_cat_opcoes(categorias: list[dict]) -> list[dict]:
    """Opções planas (categoria + subcategoria) para o autocomplete."""
    opcoes: list[dict] = []
    for c in categorias:
        opcoes.append({"cat": c["nome"], "sub": "", "label": c["nome"], "tipo": c["tipo"]})
        for s in c["subcategorias"]:
            opcoes.append(
                {
                    "cat": c["nome"],
                    "sub": s["nome"],
                    "label": f"{c['nome']} : {s['nome']}",
                    "tipo": c["tipo"],
                }
            )
    return opcoes

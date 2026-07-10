"""CRUD e operações em lote de lançamentos, com filtros de listagem."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Lancamento
from src.schemas.lancamento import (
    IdList,
    LancamentoCreate,
    LancamentoOut,
    LancamentoUpdate,
)
from src.services.regras import upsert_regra

router = APIRouter(prefix="/lancamentos", tags=["lancamentos"])


def _intervalo_mes(mes: str) -> tuple[date, date]:
    """Converte 'YYYY-MM' em (primeiro_dia, primeiro_dia_do_mes_seguinte)."""
    ano, m = (int(x) for x in mes.split("-"))
    inicio = date(ano, m, 1)
    fim = date(ano + 1, 1, 1) if m == 12 else date(ano, m + 1, 1)
    return inicio, fim


@router.get("", response_model=list[LancamentoOut])
async def listar_lancamentos(
    db: AsyncSession = Depends(get_db),
    mes: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    categoria: str | None = None,
    tipo_valor: str | None = None,
    origem: str | None = None,
    fonte: str | None = Query(default=None, pattern=r"^(fatura|extrato|manual)$"),
    confirmado: bool | None = None,
) -> list[Lancamento]:
    stmt = select(Lancamento)

    if mes:
        inicio, fim = _intervalo_mes(mes)
        stmt = stmt.where(Lancamento.data >= inicio, Lancamento.data < fim)
    if categoria:
        stmt = stmt.where(Lancamento.categoria == categoria)
    if tipo_valor:
        stmt = stmt.where(Lancamento.tipo_valor == tipo_valor)
    if origem:
        stmt = stmt.where(Lancamento.origem == origem)
    if confirmado is not None:
        stmt = stmt.where(Lancamento.confirmado == confirmado)
    if fonte == "extrato":
        stmt = stmt.where(Lancamento.arquivo.ilike("%.ofx"))
    elif fonte == "manual":
        stmt = stmt.where(Lancamento.arquivo == "manual")
    elif fonte == "fatura":
        stmt = stmt.where(
            ~Lancamento.arquivo.ilike("%.ofx"), Lancamento.arquivo != "manual"
        )

    stmt = stmt.order_by(Lancamento.data.desc(), Lancamento.id.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


@router.post("", response_model=LancamentoOut, status_code=status.HTTP_201_CREATED)
async def criar_lancamento(
    payload: LancamentoCreate, db: AsyncSession = Depends(get_db)
) -> Lancamento:
    lanc = Lancamento(**payload.model_dump())
    db.add(lanc)
    await db.commit()
    await db.refresh(lanc)
    return lanc


async def _get_lancamento(db: AsyncSession, lanc_id: int) -> Lancamento:
    lanc = (
        await db.execute(select(Lancamento).where(Lancamento.id == lanc_id))
    ).scalar_one_or_none()
    if not lanc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lançamento não encontrado.")
    return lanc


@router.put("/{lanc_id}", response_model=LancamentoOut)
async def atualizar_lancamento(
    lanc_id: int, payload: LancamentoUpdate, db: AsyncSession = Depends(get_db)
) -> Lancamento:
    lanc = await _get_lancamento(db, lanc_id)
    dados = payload.model_dump(exclude_unset=True)

    houve_correcao = "categoria" in dados or "subcategoria" in dados
    for campo, valor in dados.items():
        setattr(lanc, campo, valor)

    # Correção manual vira histórico confirmado e gera/atualiza uma regra.
    if houve_correcao or dados.get("confirmado"):
        lanc.origem = "confirmado"
        await upsert_regra(db, lanc.descricao, lanc.categoria, lanc.subcategoria)

    await db.commit()
    await db.refresh(lanc)
    return lanc


@router.delete("/{lanc_id}")
async def deletar_lancamento(lanc_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    lanc = await _get_lancamento(db, lanc_id)
    await db.delete(lanc)
    await db.commit()
    return {"mensagem": "Lançamento excluído."}


@router.post("/batch-delete")
async def batch_delete(payload: IdList, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        delete(Lancamento).where(Lancamento.id.in_(payload.ids))
    )
    await db.commit()
    return {"excluidos": result.rowcount}


@router.post("/batch-confirm")
async def batch_confirm(payload: IdList, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        update(Lancamento)
        .where(Lancamento.id.in_(payload.ids))
        .values(confirmado=True, origem="confirmado")
    )
    await db.commit()
    return {"confirmados": result.rowcount}

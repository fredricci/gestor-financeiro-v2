"""Gestão de regras de categorização."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Regra
from src.schemas.regra import RegraOut, RegrasBatch, RegraUpsert
from src.services.regras import upsert_regra

router = APIRouter(prefix="/regras", tags=["regras"])


@router.get("", response_model=list[RegraOut])
async def listar_regras(db: AsyncSession = Depends(get_db)) -> list[Regra]:
    rows = (
        await db.execute(select(Regra).order_by(Regra.descricao))
    ).scalars().all()
    return list(rows)


@router.post("", response_model=RegraOut, status_code=status.HTTP_201_CREATED)
async def salvar_regra(payload: RegraUpsert, db: AsyncSession = Depends(get_db)) -> Regra:
    regra = await upsert_regra(db, payload.descricao, payload.categoria, payload.subcategoria)
    await db.commit()
    await db.refresh(regra)
    return regra


@router.post("/batch-salvar")
async def salvar_lote(payload: RegrasBatch, db: AsyncSession = Depends(get_db)) -> dict:
    for r in payload.regras:
        await upsert_regra(db, r.descricao, r.categoria, r.subcategoria)
    await db.commit()
    return {"salvas": len(payload.regras)}


@router.delete("")
async def limpar_regras(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(delete(Regra))
    await db.commit()
    return {"removidas": result.rowcount}

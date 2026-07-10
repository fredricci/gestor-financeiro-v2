"""Atualização e remoção de subcategorias (com renomeação em cascata)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Categoria, Lancamento, Regra, Subcategoria
from src.schemas.categoria import SubcategoriaOut, SubcategoriaUpdate

router = APIRouter(prefix="/subcategorias", tags=["subcategorias"])


async def _get_sub(db: AsyncSession, sub_id: int) -> Subcategoria:
    sub = (
        await db.execute(select(Subcategoria).where(Subcategoria.id == sub_id))
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subcategoria não encontrada.")
    return sub


@router.put("/{sub_id}", response_model=SubcategoriaOut)
async def atualizar_subcategoria(
    sub_id: int, payload: SubcategoriaUpdate, db: AsyncSession = Depends(get_db)
) -> Subcategoria:
    sub = await _get_sub(db, sub_id)
    nome_antigo = sub.nome
    nome_novo = payload.nome

    cat_nome = (
        await db.execute(select(Categoria.nome).where(Categoria.id == sub.categoria_id))
    ).scalar_one()

    sub.nome = nome_novo

    if nome_antigo != nome_novo:
        await db.execute(
            update(Lancamento)
            .where(
                Lancamento.categoria == cat_nome,
                Lancamento.subcategoria == nome_antigo,
            )
            .values(subcategoria=nome_novo)
        )
        await db.execute(
            update(Regra)
            .where(Regra.categoria == cat_nome, Regra.subcategoria == nome_antigo)
            .values(subcategoria=nome_novo)
        )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Subcategoria já existe.") from None
    await db.refresh(sub)
    return sub


@router.delete("/{sub_id}")
async def deletar_subcategoria(sub_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    sub = await _get_sub(db, sub_id)
    await db.delete(sub)
    await db.commit()
    return {"mensagem": "Subcategoria removida."}

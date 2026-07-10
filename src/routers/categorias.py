"""CRUD de categorias e criação de subcategorias."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import Categoria, Lancamento, Regra, Subcategoria
from src.schemas.categoria import (
    CategoriaCreate,
    CategoriaOut,
    CategoriaUpdate,
    SubcategoriaCreate,
    SubcategoriaOut,
)

router = APIRouter(prefix="/categorias", tags=["categorias"])


async def _get_categoria(db: AsyncSession, cat_id: int) -> Categoria:
    cat = (
        await db.execute(
            select(Categoria)
            .options(selectinload(Categoria.subcategorias))
            .where(Categoria.id == cat_id)
        )
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    return cat


@router.get("", response_model=list[CategoriaOut])
async def listar_categorias(db: AsyncSession = Depends(get_db)) -> list[Categoria]:
    cats = (
        await db.execute(
            select(Categoria)
            .options(selectinload(Categoria.subcategorias))
            .order_by(Categoria.tipo, Categoria.nome)
        )
    ).scalars().all()
    return list(cats)


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
async def criar_categoria(
    payload: CategoriaCreate, db: AsyncSession = Depends(get_db)
) -> Categoria:
    cat = Categoria(nome=payload.nome, cor=payload.cor, tipo=payload.tipo)
    db.add(cat)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Categoria já existe.") from None
    return await _get_categoria(db, cat.id)


@router.put("/{cat_id}", response_model=CategoriaOut)
async def atualizar_categoria(
    cat_id: int, payload: CategoriaUpdate, db: AsyncSession = Depends(get_db)
) -> Categoria:
    cat = await _get_categoria(db, cat_id)
    nome_antigo = cat.nome
    nome_novo = payload.nome

    cat.nome = nome_novo
    cat.cor = payload.cor
    cat.tipo = payload.tipo

    # Renomeação em cascata: atualiza lançamentos e regras que referenciam o nome.
    if nome_antigo != nome_novo:
        await db.execute(
            update(Lancamento)
            .where(Lancamento.categoria == nome_antigo)
            .values(categoria=nome_novo)
        )
        await db.execute(
            update(Regra).where(Regra.categoria == nome_antigo).values(categoria=nome_novo)
        )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Categoria já existe.") from None
    return await _get_categoria(db, cat_id)


@router.delete("/{cat_id}")
async def deletar_categoria(cat_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    cat = await _get_categoria(db, cat_id)
    vinculados = (
        await db.execute(
            select(func.count())
            .select_from(Lancamento)
            .where(Lancamento.categoria == cat.nome)
        )
    ).scalar_one()
    if vinculados:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Categoria possui {vinculados} lançamento(s) vinculado(s).",
        )
    await db.delete(cat)
    await db.commit()
    return {"mensagem": "Categoria removida."}


@router.post(
    "/{cat_id}/subcategorias",
    response_model=SubcategoriaOut,
    status_code=status.HTTP_201_CREATED,
)
async def criar_subcategoria(
    cat_id: int, payload: SubcategoriaCreate, db: AsyncSession = Depends(get_db)
) -> Subcategoria:
    await _get_categoria(db, cat_id)
    sub = Subcategoria(categoria_id=cat_id, nome=payload.nome)
    db.add(sub)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Subcategoria já existe.") from None
    await db.refresh(sub)
    return sub

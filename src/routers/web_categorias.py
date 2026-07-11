"""Fragmentos HTMX da tela de Categorias (CRUD categoria/subcategoria)."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Categoria, Lancamento, Regra, Subcategoria
from src.services.consulta import fetch_categorias
from src.templating import templates

router = APIRouter(tags=["web"])


async def _render_lista(request: Request, db: AsyncSession, erro: str = "") -> HTMLResponse:
    categorias = await fetch_categorias(db)
    despesas = [c for c in categorias if c["tipo"] == "despesa"]
    receitas = [c for c in categorias if c["tipo"] == "receita"]
    return templates.TemplateResponse(
        request,
        "partials/categorias_lista.html",
        {"despesas": despesas, "receitas": receitas, "erro": erro},
    )


@router.get("/categorias/lista", response_class=HTMLResponse)
async def lista(request: Request, db: AsyncSession = Depends(get_db)):
    return await _render_lista(request, db)


@router.post("/categorias/criar", response_class=HTMLResponse)
async def criar(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nome: str = Form(...),
    tipo: str = Form("despesa"),
):
    cor = "#8b5cf6" if tipo == "despesa" else "#059669"
    db.add(Categoria(nome=nome.strip().upper(), cor=cor, tipo=tipo))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return await _render_lista(request, db, erro="Categoria já existe.")
    return await _render_lista(request, db)


@router.post("/categorias/{cat_id}/renomear", response_class=HTMLResponse)
async def renomear(
    cat_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    nome: str = Form(...),
):
    cat = (
        await db.execute(select(Categoria).where(Categoria.id == cat_id))
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    antigo, novo = cat.nome, nome.strip().upper()
    cat.nome = novo
    if antigo != novo:
        await db.execute(
            update(Lancamento).where(Lancamento.categoria == antigo).values(categoria=novo)
        )
        await db.execute(
            update(Regra).where(Regra.categoria == antigo).values(categoria=novo)
        )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return await _render_lista(request, db, erro="Já existe categoria com esse nome.")
    return await _render_lista(request, db)


@router.post("/categorias/{cat_id}/excluir", response_class=HTMLResponse)
async def excluir(cat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    cat = (
        await db.execute(select(Categoria).where(Categoria.id == cat_id))
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    vinculados = (
        await db.execute(
            select(func.count()).select_from(Lancamento).where(Lancamento.categoria == cat.nome)
        )
    ).scalar_one()
    if vinculados:
        return await _render_lista(
            request, db, erro=f"'{cat.nome}' tem {vinculados} lançamento(s) vinculado(s)."
        )
    await db.delete(cat)
    await db.commit()
    return await _render_lista(request, db)


@router.post("/categorias/{cat_id}/subcategorias/criar", response_class=HTMLResponse)
async def criar_sub(
    cat_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    nome: str = Form(...),
):
    cat = (
        await db.execute(select(Categoria).where(Categoria.id == cat_id))
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    db.add(Subcategoria(categoria_id=cat_id, nome=nome.strip()))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return await _render_lista(request, db, erro="Subcategoria já existe.")
    return await _render_lista(request, db)


@router.post("/subcategorias/{sub_id}/renomear", response_class=HTMLResponse)
async def renomear_sub(
    sub_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    nome: str = Form(...),
):
    sub = (
        await db.execute(select(Subcategoria).where(Subcategoria.id == sub_id))
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subcategoria não encontrada.")
    cat_nome = (
        await db.execute(select(Categoria.nome).where(Categoria.id == sub.categoria_id))
    ).scalar_one()
    antigo, novo = sub.nome, nome.strip()
    sub.nome = novo
    if antigo != novo:
        await db.execute(
            update(Lancamento)
            .where(Lancamento.categoria == cat_nome, Lancamento.subcategoria == antigo)
            .values(subcategoria=novo)
        )
        await db.execute(
            update(Regra)
            .where(Regra.categoria == cat_nome, Regra.subcategoria == antigo)
            .values(subcategoria=novo)
        )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return await _render_lista(request, db, erro="Já existe subcategoria com esse nome.")
    return await _render_lista(request, db)


@router.post("/subcategorias/{sub_id}/excluir", response_class=HTMLResponse)
async def excluir_sub(sub_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    sub = (
        await db.execute(select(Subcategoria).where(Subcategoria.id == sub_id))
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subcategoria não encontrada.")
    await db.delete(sub)
    await db.commit()
    return await _render_lista(request, db)

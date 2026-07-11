"""Fragmentos HTMX da tela de Lançamentos."""

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Lancamento
from src.services.consulta import fetch_lancamentos, filtrar_ordenar, lancamento_to_dict
from src.services.regras import upsert_regra
from src.templating import templates

router = APIRouter(tags=["web"])


def _parse_data(valor: str) -> date | None:
    valor = valor.strip()
    try:
        return date.fromisoformat(valor)
    except ValueError:
        pass
    partes = valor.split("/")
    if len(partes) == 3:
        d, m, y = partes
        try:
            return date(int(y), int(m), int(d))
        except ValueError:
            return None
    return None


def _parse_valor(valor: str) -> float | None:
    """Aceita '1234.56' ou o formato BR '1.234,56'."""
    txt = valor.strip()
    if not txt:
        return None
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


async def _render_tabela(request: Request, db: AsyncSession, filtros: dict) -> HTMLResponse:
    todos = await fetch_lancamentos(db)
    lista = filtrar_ordenar(todos, filtros)
    return templates.TemplateResponse(
        request,
        "partials/lancamentos_tabela.html",
        {"lancamentos": lista},
    )


async def _render_linha(request: Request, lanc: Lancamento) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "partials/lancamento_linha.html",
        {"l": lancamento_to_dict(lanc)},
    )


@router.get("/lancamentos/tabela", response_class=HTMLResponse)
async def tabela(
    request: Request,
    db: AsyncSession = Depends(get_db),
    origem: str = "todos",
    fonte: str = "todos",
    mes: str = "todos",
    busca: str = "",
    ordem: str = "data",
    direcao: str = "desc",
):
    filtros = {
        "origem": origem,
        "fonte": fonte,
        "mes": mes,
        "busca": busca,
        "ordem": ordem,
        "direcao": direcao,
    }
    return await _render_tabela(request, db, filtros)


async def _get_lanc(db: AsyncSession, lanc_id: int) -> Lancamento:
    lanc = (
        await db.execute(select(Lancamento).where(Lancamento.id == lanc_id))
    ).scalar_one_or_none()
    if not lanc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lançamento não encontrado.")
    return lanc


@router.get("/lancamentos/{lanc_id}/linha", response_class=HTMLResponse)
async def linha(lanc_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    lanc = await _get_lanc(db, lanc_id)
    return await _render_linha(request, lanc)


@router.post("/lancamentos/inline-update/{lanc_id}", response_class=HTMLResponse)
async def inline_update(
    lanc_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    data: str | None = Form(default=None),
    valor: str | None = Form(default=None),
    tipo_valor: str | None = Form(default=None),
    categoria: str | None = Form(default=None),
    subcategoria: str | None = Form(default=None),
    confirmado: bool | None = Form(default=None),
):
    lanc = await _get_lanc(db, lanc_id)

    if data is not None:
        parsed = _parse_data(data)
        if parsed:
            lanc.data = parsed
    if valor is not None:
        v = _parse_valor(valor)
        if v is not None and v > 0:
            lanc.valor = v
    if tipo_valor in ("entrada", "saida"):
        lanc.tipo_valor = tipo_valor

    houve_correcao = categoria is not None or subcategoria is not None
    if categoria is not None:
        lanc.categoria = categoria
    if subcategoria is not None:
        lanc.subcategoria = subcategoria

    if houve_correcao or confirmado:
        lanc.confirmado = True
        lanc.origem = "confirmado"
        await upsert_regra(db, lanc.descricao, lanc.categoria, lanc.subcategoria)

    await db.commit()
    await db.refresh(lanc)
    return await _render_linha(request, lanc)


@router.post("/lancamentos/novo", response_class=HTMLResponse)
async def novo(
    request: Request,
    db: AsyncSession = Depends(get_db),
    data: str = Form(...),
    descricao: str = Form(...),
    valor: float = Form(...),
    tipo_valor: str = Form("saida"),
    categoria: str = Form("NAO LEMBRO"),
    subcategoria: str = Form(""),
):
    dt = _parse_data(data) or date.today()
    lanc = Lancamento(
        data=dt,
        descricao=descricao.strip(),
        valor=abs(valor),
        tipo_valor=tipo_valor if tipo_valor in ("entrada", "saida") else "saida",
        categoria=categoria or "NAO LEMBRO",
        subcategoria=subcategoria or "",
        origem="manual",
        confianca="alta",
        confirmado=True,
        arquivo="manual",
    )
    db.add(lanc)
    if categoria and categoria != "NAO LEMBRO":
        await upsert_regra(db, descricao, categoria, subcategoria)
    await db.commit()

    resp = await _render_tabela(request, db, {})
    resp.headers["HX-Trigger"] = "lancamentoCriado"
    return resp


@router.post("/lancamentos/batch-confirmar", response_class=HTMLResponse)
async def batch_confirmar(
    request: Request,
    db: AsyncSession = Depends(get_db),
    ids: list[int] = Form(default=[]),
):
    if ids:
        await db.execute(
            update(Lancamento)
            .where(Lancamento.id.in_(ids))
            .values(confirmado=True, origem="confirmado")
        )
        await db.commit()
    return await _render_tabela(request, db, {})


@router.post("/lancamentos/batch-excluir", response_class=HTMLResponse)
async def batch_excluir(
    request: Request,
    db: AsyncSession = Depends(get_db),
    ids: list[int] = Form(default=[]),
):
    if ids:
        for lanc_id in ids:
            lanc = (
                await db.execute(select(Lancamento).where(Lancamento.id == lanc_id))
            ).scalar_one_or_none()
            if lanc:
                await db.delete(lanc)
        await db.commit()
    return await _render_tabela(request, db, {})

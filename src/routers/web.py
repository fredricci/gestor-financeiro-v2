"""Rotas de páginas HTML (Jinja2 + HTMX)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.consulta import (
    build_cat_opcoes,
    compute_metricas,
    fetch_categorias,
    fetch_lancamentos,
    filtrar_ordenar,
    meses_disponiveis,
)
from src.services.relatorio import montar_relatorio
from src.templating import templates

router = APIRouter(tags=["web"])


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="/upload")


@router.get("/upload", response_class=HTMLResponse)
async def pagina_upload(request: Request, db: AsyncSession = Depends(get_db)):
    metricas = await compute_metricas(db)
    return templates.TemplateResponse(
        request,
        "pages/upload.html",
        {"pagina": "upload", "metricas": metricas},
    )


@router.get("/upload/metricas", response_class=HTMLResponse)
async def fragmento_metricas(request: Request, db: AsyncSession = Depends(get_db)):
    metricas = await compute_metricas(db)
    return templates.TemplateResponse(
        request,
        "partials/metrics.html", {"metricas": metricas}
    )


@router.get("/lancamentos", response_class=HTMLResponse)
async def pagina_lancamentos(request: Request, db: AsyncSession = Depends(get_db)):
    todos = await fetch_lancamentos(db)
    categorias = await fetch_categorias(db)
    lista = filtrar_ordenar(todos, {})
    return templates.TemplateResponse(
        request,
        "pages/lancamentos.html",
        {
            "pagina": "lancamentos",
            "lancamentos": lista,
            "categorias": categorias,
            "cat_opcoes": build_cat_opcoes(categorias),
            "meses": meses_disponiveis(todos),
            "filtros": {"origem": "todos", "fonte": "todos", "mes": "todos"},
        },
    )


@router.get("/grafico", response_class=HTMLResponse)
async def pagina_grafico(request: Request, db: AsyncSession = Depends(get_db)):
    todos = await fetch_lancamentos(db)
    categorias = await fetch_categorias(db)
    relatorio = montar_relatorio(todos, categorias)
    return templates.TemplateResponse(
        request,
        "pages/grafico.html",
        {"pagina": "grafico", "relatorio": relatorio},
    )


@router.get("/categorias", response_class=HTMLResponse)
async def pagina_categorias(request: Request, db: AsyncSession = Depends(get_db)):
    categorias = await fetch_categorias(db)
    return templates.TemplateResponse(
        request,
        "pages/categorias.html",
        {
            "pagina": "categorias",
            "despesas": [c for c in categorias if c["tipo"] == "despesa"],
            "receitas": [c for c in categorias if c["tipo"] == "receita"],
        },
    )

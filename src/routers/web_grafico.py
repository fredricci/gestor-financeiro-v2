"""Fragmento HTMX: modal de detalhes de uma célula do relatório."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.consulta import fetch_lancamentos
from src.templating import mes_label, templates

router = APIRouter(tags=["web"])


@router.get("/grafico/detalhe", response_class=HTMLResponse)
async def detalhe(
    request: Request,
    db: AsyncSession = Depends(get_db),
    categoria: str = "",
    subcategoria: str = "",
    mes: str = "todos",
):
    todos = await fetch_lancamentos(db)
    lista = [x for x in todos if x["categoria"] == categoria]
    if subcategoria and subcategoria != "todos":
        alvo = "" if subcategoria == "—" else subcategoria
        lista = [x for x in lista if (x["subcategoria"] or "") == alvo]
    if mes and mes != "todos":
        lista = [x for x in lista if str(x["data"])[:7] == mes]

    saidas = sorted(
        [x for x in lista if x["tipo_valor"] == "saida"],
        key=lambda x: x["data"],
        reverse=True,
    )
    entradas = sorted(
        [x for x in lista if x["tipo_valor"] == "entrada"],
        key=lambda x: x["data"],
        reverse=True,
    )
    total_sai = sum(x["valor"] for x in saidas)
    total_ent = sum(x["valor"] for x in entradas)
    if total_sai == 0:
        liquido = total_ent
    elif total_ent == 0:
        liquido = total_sai
    else:
        liquido = total_sai - total_ent

    titulo = categoria
    if subcategoria and subcategoria not in ("", "todos", "—"):
        titulo = f"{categoria} : {subcategoria}"
    sub = mes_label(mes) if mes and mes != "todos" else "todos os meses"

    return templates.TemplateResponse(
        request,
        "partials/modal_detalhe.html",
        {
            "titulo": titulo,
            "subtitulo": sub,
            "saidas": saidas,
            "entradas": entradas,
            "total_saidas": total_sai,
            "total_entradas": total_ent,
            "liquido": liquido,
            "count": len(lista),
        },
    )

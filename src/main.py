"""Aplicação FastAPI: API REST (/api) + frontend Jinja2/HTMX."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.logging_config import configure_logging
from src.routers import (
    categorias,
    categorizar,
    health,
    lancamentos,
    regras,
    subcategorias,
    upload,
    web,
    web_categorias,
    web_grafico,
    web_lancamentos,
)

configure_logging()

app = FastAPI(title="Gestor Financeiro", version="0.3.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

# API REST (JSON) sob /api
app.include_router(health.router)
app.include_router(categorias.router, prefix="/api")
app.include_router(subcategorias.router, prefix="/api")
app.include_router(lancamentos.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(categorizar.router, prefix="/api")
app.include_router(regras.router, prefix="/api")

# Frontend (HTML/HTMX)
app.include_router(web.router)
app.include_router(web_lancamentos.router)
app.include_router(web_grafico.router)
app.include_router(web_categorias.router)

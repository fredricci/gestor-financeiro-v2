"""Aplicação FastAPI: monta os routers da API REST."""

from fastapi import FastAPI

from src.logging_config import configure_logging
from src.routers import (
    categorias,
    categorizar,
    health,
    lancamentos,
    regras,
    subcategorias,
    upload,
)

configure_logging()

app = FastAPI(title="Gestor Financeiro", version="0.2.0")

app.include_router(health.router)
app.include_router(categorias.router, prefix="/api")
app.include_router(subcategorias.router, prefix="/api")
app.include_router(lancamentos.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(categorizar.router, prefix="/api")
app.include_router(regras.router, prefix="/api")

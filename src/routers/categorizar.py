"""Endpoint de sugestão de categorias (regras + IA, sem persistência)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_categorizer
from src.schemas.categorizar import CategorizarRequest, CategorizarResultado
from src.services.categorizacao import sugerir_categorias
from src.services.claude_client import Categorizer

router = APIRouter(prefix="/categorizar", tags=["categorizar"])


@router.post("", response_model=list[CategorizarResultado])
async def categorizar(
    payload: CategorizarRequest,
    db: AsyncSession = Depends(get_db),
    categorizer: Categorizer = Depends(get_categorizer),
) -> list[dict]:
    itens = [item.model_dump() for item in payload.lancamentos]
    return await sugerir_categorias(db, itens, categorizer)

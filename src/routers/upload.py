"""Upload de faturas (CSV) e extratos (OFX): parse, dedup, categorização e persistência."""

from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_categorizer
from src.logging_config import get_logger
from src.models import Lancamento
from src.schemas.upload import UploadResumo
from src.services.categorizacao import sugerir_categorias
from src.services.claude_client import Categorizer
from src.services.csv_parser import parse_csv
from src.services.ofx_parser import parse_ofx

router = APIRouter(prefix="/upload", tags=["upload"])
logger = get_logger(__name__)


def _parse_data(valor: str) -> date | None:
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


async def _persistir(
    db: AsyncSession,
    novos: list[dict],
    categorizer: Categorizer,
    arquivo: str,
) -> tuple[list[Lancamento], Counter]:
    """Categoriza os itens novos, cria os lançamentos e retorna (lista, contagem_origem)."""
    if not novos:
        return [], Counter()

    sugestoes = await sugerir_categorias(db, novos, categorizer)
    criados: list[Lancamento] = []
    por_origem: Counter = Counter()

    for item, sug in zip(novos, sugestoes, strict=True):
        lanc = Lancamento(
            data=item["_data"],
            descricao=item["descricao"],
            valor=item["valor"],
            tipo_valor=item.get("tipo_valor", "saida"),
            categoria=sug["categoria"],
            subcategoria=sug.get("subcategoria", ""),
            origem=sug["origem"],
            confianca=sug["confianca"],
            confirmado=False,
            arquivo=arquivo,
            fitid=item.get("fitid", ""),
        )
        db.add(lanc)
        criados.append(lanc)
        por_origem[sug["origem"]] += 1

    await db.commit()
    for lanc in criados:
        await db.refresh(lanc)
    return criados, por_origem


@router.post("/csv", response_model=UploadResumo)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    categorizer: Categorizer = Depends(get_categorizer),
) -> UploadResumo:
    conteudo = (await file.read()).decode("utf-8-sig", errors="replace")
    linhas = parse_csv(conteudo, arquivo=file.filename or "")

    # Deduplicação por (data, descricao, valor).
    existentes = {
        (d.isoformat(), desc, str(val))
        for d, desc, val in (
            await db.execute(
                select(Lancamento.data, Lancamento.descricao, Lancamento.valor)
            )
        ).all()
    }

    novos: list[dict] = []
    duplicados = 0
    for linha in linhas:
        data = _parse_data(linha.data)
        if data is None:
            continue
        chave = (data.isoformat(), linha.descricao, str(linha.valor))
        if chave in existentes:
            duplicados += 1
            continue
        existentes.add(chave)
        novos.append(
            {
                "_data": data,
                "descricao": linha.descricao,
                "valor": linha.valor,
                "tipo_valor": linha.tipo_valor,
            }
        )

    criados, por_origem = await _persistir(db, novos, categorizer, file.filename or "")
    logger.info(
        "upload_csv", arquivo=file.filename, lidos=len(linhas), novos=len(criados),
        duplicados=duplicados,
    )
    return UploadResumo(
        arquivo=file.filename or "",
        total_lidos=len(linhas),
        novos=len(criados),
        duplicados=duplicados,
        por_origem=dict(por_origem),
        lancamentos=criados,
    )


@router.post("/ofx", response_model=UploadResumo)
async def upload_ofx(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    categorizer: Categorizer = Depends(get_categorizer),
) -> UploadResumo:
    conteudo = (await file.read()).decode("latin-1", errors="replace")
    linhas = parse_ofx(conteudo)

    # Deduplicação por FITID (quando presente).
    fitids_existentes = {
        f
        for (f,) in (
            await db.execute(
                select(Lancamento.fitid).where(Lancamento.fitid != "")
            )
        ).all()
    }

    novos: list[dict] = []
    duplicados = 0
    vistos: set[str] = set()
    for linha in linhas:
        data = _parse_data(linha.data)
        if data is None:
            continue
        if linha.fitid and (linha.fitid in fitids_existentes or linha.fitid in vistos):
            duplicados += 1
            continue
        if linha.fitid:
            vistos.add(linha.fitid)
        novos.append(
            {
                "_data": data,
                "descricao": linha.descricao,
                "valor": linha.valor,
                "tipo_valor": linha.tipo_valor,
                "fitid": linha.fitid,
            }
        )

    criados, por_origem = await _persistir(db, novos, categorizer, file.filename or "")
    logger.info(
        "upload_ofx", arquivo=file.filename, lidos=len(linhas), novos=len(criados),
        duplicados=duplicados,
    )
    return UploadResumo(
        arquivo=file.filename or "",
        total_lidos=len(linhas),
        novos=len(criados),
        duplicados=duplicados,
        por_origem=dict(por_origem),
        lancamentos=criados,
    )

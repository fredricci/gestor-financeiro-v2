"""Fixtures de teste: banco SQLite in-memory e cliente HTTP com IA mockada."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.database import get_db
from src.dependencies import get_categorizer
from src.main import app
from src.models import Base, Categoria, Subcategoria


class FakeCategorizer:
    """Categorizador falso e determinístico para os testes.

    Por padrão devolve NAO LEMBRO. Pode receber um mapeamento
    descricao_substring -> (categoria, subcategoria) e uma flag de erro.
    """

    def __init__(
        self,
        mapa: dict[str, tuple[str, str]] | None = None,
        falhar: bool = False,
    ) -> None:
        self.mapa = mapa or {}
        self.falhar = falhar
        self.chamadas: list[list[dict]] = []

    async def categorizar(
        self, itens: list[dict], historico: list[tuple[str, str, str]]
    ) -> list[dict]:
        self.chamadas.append(itens)
        resultados = []
        for it in itens:
            categoria, sub, origem, conf = "NAO LEMBRO", "", "ia", "baixa"
            if self.falhar:
                categoria, origem, conf = "NAO LEMBRO", "erro", "baixa"
            else:
                for chave, (cat, s) in self.mapa.items():
                    if chave.upper() in it["descricao"].upper():
                        categoria, sub, conf = cat, s, "alta"
                        break
            resultados.append(
                {
                    "descricao": it["descricao"],
                    "categoria": categoria,
                    "subcategoria": sub,
                    "confianca": conf,
                    "origem": origem,
                    "tipo_valor": it.get("tipo_valor", "saida"),
                }
            )
        return resultados


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def fake_categorizer() -> FakeCategorizer:
    return FakeCategorizer()


@pytest_asyncio.fixture
async def client(
    session_maker, fake_categorizer
) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_categorizer] = lambda: fake_categorizer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_categorias(session_maker) -> None:
    """Insere algumas categorias e subcategorias mínimas para os testes."""
    async with session_maker() as s:
        alim = Categoria(nome="ALIMENTACAO", cor="#8b5cf6", tipo="despesa")
        transp = Categoria(nome="TRANSPORTE", cor="#8b5cf6", tipo="despesa")
        s.add_all([alim, transp, Categoria(nome="SALARIO FRED", cor="#059669", tipo="receita")])
        await s.flush()
        s.add(Subcategoria(categoria_id=alim.id, nome="Delivery"))
        s.add(Subcategoria(categoria_id=transp.id, nome="Uber Taxi Metro"))
        await s.commit()

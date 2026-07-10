import pytest

from src.models import Regra
from src.services.categorizacao import sugerir_categorias
from tests.conftest import FakeCategorizer


@pytest.mark.asyncio
async def test_regra_exata_tem_prioridade_sobre_ia(session_maker):
    async with session_maker() as s:
        s.add(Regra(descricao="UBER TRIP", categoria="TRANSPORTE", subcategoria="Uber Taxi Metro"))
        await s.commit()

    fake = FakeCategorizer(mapa={"UBER": ("EXTRAS", "")})
    async with session_maker() as s:
        res = await sugerir_categorias(
            s, [{"descricao": "UBER TRIP", "tipo_valor": "saida"}], fake
        )
    assert res[0]["categoria"] == "TRANSPORTE"
    assert res[0]["origem"] == "regra_usuario"
    assert fake.chamadas == []  # IA nem foi chamada


@pytest.mark.asyncio
async def test_regra_substring(session_maker):
    async with session_maker() as s:
        s.add(Regra(descricao="COBASI", categoria="BEBEL", subcategoria="Racao Banho Tosa Vet"))
        await s.commit()

    fake = FakeCategorizer()
    async with session_maker() as s:
        res = await sugerir_categorias(
            s, [{"descricao": "COBASI LOJA 22 SP", "tipo_valor": "saida"}], fake
        )
    assert res[0]["categoria"] == "BEBEL"
    assert res[0]["origem"] == "regra_usuario"


@pytest.mark.asyncio
async def test_sem_regra_usa_ia(session_maker):
    fake = FakeCategorizer(mapa={"PADARIA": ("ALIMENTACAO", "Refeições")})
    async with session_maker() as s:
        res = await sugerir_categorias(
            s, [{"descricao": "PADARIA DO ZE", "tipo_valor": "saida"}], fake
        )
    assert res[0]["categoria"] == "ALIMENTACAO"
    assert res[0]["origem"] == "ia"
    assert len(fake.chamadas) == 1


@pytest.mark.asyncio
async def test_mix_regra_e_ia_mantem_ordem(session_maker):
    async with session_maker() as s:
        s.add(Regra(descricao="UBER", categoria="TRANSPORTE", subcategoria=""))
        await s.commit()

    fake = FakeCategorizer(mapa={"PADARIA": ("ALIMENTACAO", "")})
    itens = [
        {"descricao": "UBER", "tipo_valor": "saida"},
        {"descricao": "PADARIA", "tipo_valor": "saida"},
    ]
    async with session_maker() as s:
        res = await sugerir_categorias(s, itens, fake)
    assert [r["categoria"] for r in res] == ["TRANSPORTE", "ALIMENTACAO"]
    assert [r["origem"] for r in res] == ["regra_usuario", "ia"]

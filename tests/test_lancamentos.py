import pytest


async def _cria(client, **over):
    payload = {
        "data": "2026-01-15",
        "descricao": "TESTE",
        "valor": 42.50,
        "tipo_valor": "saida",
        "categoria": "NAO LEMBRO",
    }
    payload.update(over)
    return await client.post("/api/lancamentos", json=payload)


@pytest.mark.asyncio
async def test_criar_e_recuperar_lancamento(client):
    resp = await _cria(client, descricao="MERCADO CENTRAL")
    assert resp.status_code == 201
    body = resp.json()
    assert body["descricao"] == "MERCADO CENTRAL"
    assert body["fonte"] == "manual"  # arquivo default = manual

    lista = (await client.get("/api/lancamentos")).json()
    assert len(lista) == 1
    assert lista[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_atualizar_lancamento_gera_regra(client):
    lanc = (await _cria(client, descricao="POSTO SHELL")).json()
    resp = await client.put(
        f"/api/lancamentos/{lanc['id']}",
        json={"categoria": "TRANSPORTE", "subcategoria": "Combustivel"},
    )
    assert resp.status_code == 200
    assert resp.json()["categoria"] == "TRANSPORTE"
    assert resp.json()["origem"] == "confirmado"

    regras = (await client.get("/api/regras")).json()
    assert any(r["descricao"] == "POSTO SHELL" for r in regras)


@pytest.mark.asyncio
async def test_deletar_lancamento(client):
    lanc = (await _cria(client)).json()
    resp = await client.delete(f"/api/lancamentos/{lanc['id']}")
    assert resp.status_code == 200
    assert (await client.get("/api/lancamentos")).json() == []


@pytest.mark.asyncio
async def test_batch_delete(client):
    ids = [(await _cria(client, descricao=f"L{i}")).json()["id"] for i in range(3)]
    resp = await client.post("/api/lancamentos/batch-delete", json={"ids": ids[:2]})
    assert resp.status_code == 200
    assert resp.json()["excluidos"] == 2
    restantes = (await client.get("/api/lancamentos")).json()
    assert len(restantes) == 1


@pytest.mark.asyncio
async def test_batch_confirm(client):
    ids = [(await _cria(client, descricao=f"L{i}")).json()["id"] for i in range(2)]
    resp = await client.post("/api/lancamentos/batch-confirm", json={"ids": ids})
    assert resp.json()["confirmados"] == 2
    lista = (await client.get("/api/lancamentos")).json()
    assert all(_l["confirmado"] for _l in lista)


@pytest.mark.asyncio
async def test_filtro_mes(client):
    await _cria(client, data="2026-01-10", descricao="JAN")
    await _cria(client, data="2026-02-10", descricao="FEV")
    lista = (await client.get("/api/lancamentos", params={"mes": "2026-01"})).json()
    assert len(lista) == 1
    assert lista[0]["descricao"] == "JAN"


@pytest.mark.asyncio
async def test_filtro_tipo_valor_e_categoria(client):
    await _cria(client, descricao="SAIDA1", tipo_valor="saida", categoria="ALIMENTACAO")
    await _cria(
        client,
        descricao="ENTRADA1",
        tipo_valor="entrada",
        categoria="SALARIO FRED",
        valor=1000,
    )
    entradas = (
        await client.get("/api/lancamentos", params={"tipo_valor": "entrada"})
    ).json()
    assert len(entradas) == 1 and entradas[0]["descricao"] == "ENTRADA1"

    alim = (
        await client.get("/api/lancamentos", params={"categoria": "ALIMENTACAO"})
    ).json()
    assert len(alim) == 1 and alim[0]["descricao"] == "SAIDA1"


@pytest.mark.asyncio
async def test_filtro_fonte(client):
    await _cria(client, descricao="MANUAL1")  # arquivo = manual
    await _cria(client, descricao="FATURA1", arquivo="fatura_jan.csv")
    await _cria(client, descricao="EXTRATO1", arquivo="extrato.ofx")

    manual = (await client.get("/api/lancamentos", params={"fonte": "manual"})).json()
    assert {_l["descricao"] for _l in manual} == {"MANUAL1"}

    fatura = (await client.get("/api/lancamentos", params={"fonte": "fatura"})).json()
    assert {_l["descricao"] for _l in fatura} == {"FATURA1"}

    extrato = (await client.get("/api/lancamentos", params={"fonte": "extrato"})).json()
    assert {_l["descricao"] for _l in extrato} == {"EXTRATO1"}

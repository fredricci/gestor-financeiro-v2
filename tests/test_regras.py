import pytest


@pytest.mark.asyncio
async def test_criar_regra_normaliza_descricao(client):
    resp = await client.post(
        "/api/regras", json={"descricao": "  uber trip  ", "categoria": "TRANSPORTE"}
    )
    assert resp.status_code == 201
    assert resp.json()["descricao"] == "UBER TRIP"


@pytest.mark.asyncio
async def test_upsert_atualiza_regra_existente(client):
    await client.post("/api/regras", json={"descricao": "IFOOD", "categoria": "EXTRAS"})
    await client.post(
        "/api/regras",
        json={"descricao": "IFOOD", "categoria": "ALIMENTACAO", "subcategoria": "Delivery"},
    )
    regras = (await client.get("/api/regras")).json()
    ifood = [r for r in regras if r["descricao"] == "IFOOD"]
    assert len(ifood) == 1
    assert ifood[0]["categoria"] == "ALIMENTACAO"


@pytest.mark.asyncio
async def test_batch_salvar(client):
    resp = await client.post(
        "/api/regras/batch-salvar",
        json={
            "regras": [
                {"descricao": "UBER", "categoria": "TRANSPORTE"},
                {"descricao": "COBASI", "categoria": "BEBEL"},
            ]
        },
    )
    assert resp.json()["salvas"] == 2
    assert len((await client.get("/api/regras")).json()) == 2


@pytest.mark.asyncio
async def test_limpar_regras(client):
    await client.post("/api/regras", json={"descricao": "X", "categoria": "EXTRAS"})
    resp = await client.delete("/api/regras")
    assert resp.json()["removidas"] == 1
    assert (await client.get("/api/regras")).json() == []

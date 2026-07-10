import pytest


@pytest.mark.asyncio
async def test_criar_e_listar_categoria(client):
    resp = await client.post("/api/categorias", json={"nome": "lazer", "cor": "#8b5cf6"})
    assert resp.status_code == 201
    assert resp.json()["nome"] == "LAZER"  # nome normalizado em maiúsculas

    lista = (await client.get("/api/categorias")).json()
    assert any(c["nome"] == "LAZER" for c in lista)


@pytest.mark.asyncio
async def test_categoria_duplicada_retorna_400(client):
    await client.post("/api/categorias", json={"nome": "SAUDE"})
    resp = await client.post("/api/categorias", json={"nome": "SAUDE"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_listar_traz_subcategorias_aninhadas(client, seed_categorias):
    lista = (await client.get("/api/categorias")).json()
    alim = next(c for c in lista if c["nome"] == "ALIMENTACAO")
    nomes = {s["nome"] for s in alim["subcategorias"]}
    assert "Delivery" in nomes


@pytest.mark.asyncio
async def test_criar_subcategoria(client):
    cat = (await client.post("/api/categorias", json={"nome": "SAUDE"})).json()
    resp = await client.post(
        f"/api/categorias/{cat['id']}/subcategorias", json={"nome": "Farmacia"}
    )
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Farmacia"


@pytest.mark.asyncio
async def test_renomear_categoria_cascateia_em_lancamentos_e_regras(client):
    cat = (await client.post("/api/categorias", json={"nome": "MERCADO"})).json()
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-01-10",
            "descricao": "COMPRA X",
            "valor": 10,
            "categoria": "MERCADO",
        },
    )
    await client.post(
        "/api/regras", json={"descricao": "COMPRA X", "categoria": "MERCADO"}
    )

    resp = await client.put(
        f"/api/categorias/{cat['id']}",
        json={"nome": "ALIMENTACAO", "cor": "#8b5cf6", "tipo": "despesa"},
    )
    assert resp.status_code == 200

    lancs = (await client.get("/api/lancamentos")).json()
    assert lancs[0]["categoria"] == "ALIMENTACAO"
    regras = (await client.get("/api/regras")).json()
    assert regras[0]["categoria"] == "ALIMENTACAO"


@pytest.mark.asyncio
async def test_deletar_categoria_com_lancamento_bloqueia(client):
    cat = (await client.post("/api/categorias", json={"nome": "MERCADO"})).json()
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-01-10",
            "descricao": "COMPRA X",
            "valor": 10,
            "categoria": "MERCADO",
        },
    )
    resp = await client.delete(f"/api/categorias/{cat['id']}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_deletar_categoria_sem_vinculo_ok(client):
    cat = (await client.post("/api/categorias", json={"nome": "TEMP"})).json()
    resp = await client.delete(f"/api/categorias/{cat['id']}")
    assert resp.status_code == 200
    lista = (await client.get("/api/categorias")).json()
    assert not any(c["nome"] == "TEMP" for c in lista)

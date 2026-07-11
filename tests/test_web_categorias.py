import pytest


@pytest.mark.asyncio
async def test_lista_fragmento(client, seed_categorias):
    resp = await client.get("/categorias/lista")
    assert resp.status_code == 200
    assert "ALIMENTACAO" in resp.text
    assert 'id="cat-lista"' in resp.text


@pytest.mark.asyncio
async def test_criar_categoria_via_form(client):
    resp = await client.post("/categorias/criar", data={"nome": "lazer", "tipo": "despesa"})
    assert resp.status_code == 200
    assert "LAZER" in resp.text


@pytest.mark.asyncio
async def test_criar_categoria_duplicada_mostra_erro(client, seed_categorias):
    resp = await client.post(
        "/categorias/criar", data={"nome": "ALIMENTACAO", "tipo": "despesa"}
    )
    assert resp.status_code == 200
    assert "já existe" in resp.text.lower()


@pytest.mark.asyncio
async def test_renomear_categoria_cascateia(client, seed_categorias):
    cats = (await client.get("/api/categorias")).json()
    alim = next(c for c in cats if c["nome"] == "ALIMENTACAO")

    await client.post(
        "/api/lancamentos",
        json={"data": "2026-06-01", "descricao": "X", "valor": 10, "categoria": "ALIMENTACAO"},
    )
    resp = await client.post(f"/categorias/{alim['id']}/renomear", data={"nome": "COMIDA"})
    assert resp.status_code == 200
    assert "COMIDA" in resp.text

    lancs = (await client.get("/api/lancamentos")).json()
    assert lancs[0]["categoria"] == "COMIDA"


@pytest.mark.asyncio
async def test_excluir_categoria_com_lancamento_mostra_erro(client, seed_categorias):
    cats = (await client.get("/api/categorias")).json()
    alim = next(c for c in cats if c["nome"] == "ALIMENTACAO")
    await client.post(
        "/api/lancamentos",
        json={"data": "2026-06-01", "descricao": "X", "valor": 10, "categoria": "ALIMENTACAO"},
    )
    resp = await client.post(f"/categorias/{alim['id']}/excluir")
    assert resp.status_code == 200
    assert "lançamento" in resp.text.lower()
    assert "ALIMENTACAO" in resp.text  # categoria continua na lista


@pytest.mark.asyncio
async def test_criar_e_excluir_subcategoria(client, seed_categorias):
    cats = (await client.get("/api/categorias")).json()
    alim = next(c for c in cats if c["nome"] == "ALIMENTACAO")

    resp = await client.post(
        f"/categorias/{alim['id']}/subcategorias/criar", data={"nome": "Refeições"}
    )
    assert resp.status_code == 200
    assert "Refeições" in resp.text

    subs = (await client.get("/api/categorias")).json()
    sub_id = next(
        s["id"] for c in subs if c["nome"] == "ALIMENTACAO" for s in c["subcategorias"]
        if s["nome"] == "Refeições"
    )
    resp2 = await client.post(f"/subcategorias/{sub_id}/excluir")
    assert resp2.status_code == 200
    assert "Refeições" not in resp2.text


@pytest.mark.asyncio
async def test_renomear_subcategoria_cascateia(client, seed_categorias):
    cats = (await client.get("/api/categorias")).json()
    alim = next(c for c in cats if c["nome"] == "ALIMENTACAO")
    sub_id = next(s["id"] for s in alim["subcategorias"] if s["nome"] == "Delivery")

    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-06-01", "descricao": "X", "valor": 10,
            "categoria": "ALIMENTACAO", "subcategoria": "Delivery",
        },
    )
    resp = await client.post(f"/subcategorias/{sub_id}/renomear", data={"nome": "Entregas"})
    assert resp.status_code == 200

    lancs = (await client.get("/api/lancamentos")).json()
    assert lancs[0]["subcategoria"] == "Entregas"

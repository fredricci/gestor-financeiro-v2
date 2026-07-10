import pytest


async def _cria_cat_com_sub(client, cat_nome, sub_nome):
    cat = (await client.post("/api/categorias", json={"nome": cat_nome})).json()
    sub = (
        await client.post(
            f"/api/categorias/{cat['id']}/subcategorias", json={"nome": sub_nome}
        )
    ).json()
    return cat, sub


@pytest.mark.asyncio
async def test_atualizar_subcategoria(client):
    _, sub = await _cria_cat_com_sub(client, "SAUDE", "Farmacia")
    resp = await client.put(f"/api/subcategorias/{sub['id']}", json={"nome": "Farmácia"})
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Farmácia"


@pytest.mark.asyncio
async def test_renomear_subcategoria_cascateia(client):
    cat, sub = await _cria_cat_com_sub(client, "SAUDE", "Farmacia")
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-01-10",
            "descricao": "DROGARIA",
            "valor": 20,
            "categoria": "SAUDE",
            "subcategoria": "Farmacia",
        },
    )
    await client.put(f"/api/subcategorias/{sub['id']}", json={"nome": "Farmácia"})
    lancs = (await client.get("/api/lancamentos")).json()
    assert lancs[0]["subcategoria"] == "Farmácia"


@pytest.mark.asyncio
async def test_deletar_subcategoria(client):
    _, sub = await _cria_cat_com_sub(client, "SAUDE", "Suplementos")
    resp = await client.delete(f"/api/subcategorias/{sub['id']}")
    assert resp.status_code == 200
    resp2 = await client.put(f"/api/subcategorias/{sub['id']}", json={"nome": "X"})
    assert resp2.status_code == 404

import pytest


@pytest.mark.asyncio
async def test_grafico_pagina_com_dados(client):
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-06-05", "descricao": "PADARIA", "valor": 100,
            "categoria": "ALIMENTACAO", "tipo_valor": "saida",
        },
    )
    resp = await client.get("/grafico")
    assert resp.status_code == 200
    assert "ALIMENTACAO" in resp.text
    assert "chart-data" in resp.text


@pytest.mark.asyncio
async def test_grafico_detalhe_fragmento(client):
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-06-05", "descricao": "PADARIA", "valor": 100,
            "categoria": "ALIMENTACAO", "tipo_valor": "saida",
        },
    )
    resp = await client.get(
        "/grafico/detalhe", params={"categoria": "ALIMENTACAO", "mes": "2026-06"}
    )
    assert resp.status_code == 200
    assert "PADARIA" in resp.text
    assert "1 lançamento(s)" in resp.text


@pytest.mark.asyncio
async def test_grafico_detalhe_filtra_por_subcategoria(client):
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-06-05", "descricao": "IFOOD", "valor": 40,
            "categoria": "ALIMENTACAO", "subcategoria": "Delivery", "tipo_valor": "saida",
        },
    )
    await client.post(
        "/api/lancamentos",
        json={
            "data": "2026-06-06", "descricao": "MERCADO", "valor": 60,
            "categoria": "ALIMENTACAO", "subcategoria": "Supermercado", "tipo_valor": "saida",
        },
    )
    resp = await client.get(
        "/grafico/detalhe",
        params={"categoria": "ALIMENTACAO", "subcategoria": "Delivery", "mes": "todos"},
    )
    assert "IFOOD" in resp.text
    assert "MERCADO" not in resp.text

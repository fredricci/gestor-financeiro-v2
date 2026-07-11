import pytest


@pytest.mark.asyncio
async def test_home_redireciona_para_upload(client):
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/upload"


@pytest.mark.asyncio
async def test_pagina_upload_ok(client, seed_categorias):
    resp = await client.get("/upload")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Carregue sua fatura" in resp.text


@pytest.mark.asyncio
async def test_pagina_lancamentos_ok(client, seed_categorias):
    resp = await client.get("/lancamentos")
    assert resp.status_code == 200
    assert "Lançamentos" in resp.text
    assert "tbody-lancamentos" in resp.text


@pytest.mark.asyncio
async def test_pagina_grafico_vazio_ok(client):
    resp = await client.get("/grafico")
    assert resp.status_code == 200
    assert "Nenhum lançamento carregado" in resp.text


@pytest.mark.asyncio
async def test_pagina_categorias_ok(client, seed_categorias):
    resp = await client.get("/categorias")
    assert resp.status_code == 200
    assert "ALIMENTACAO" in resp.text
    assert "SALARIO FRED" in resp.text


@pytest.mark.asyncio
async def test_upload_metricas_fragmento(client):
    resp = await client.get("/upload/metricas")
    assert resp.status_code == 200
    assert 'id="metrics"' in resp.text

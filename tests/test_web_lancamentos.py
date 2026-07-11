import pytest


async def _cria_lancamento(client, **over):
    payload = {
        "data": "2026-06-10",
        "descricao": "TESTE WEB",
        "valor": 42.5,
        "tipo_valor": "saida",
        "categoria": "NAO LEMBRO",
    }
    payload.update(over)
    resp = await client.post("/api/lancamentos", json=payload)
    return resp.json()


@pytest.mark.asyncio
async def test_tabela_fragmento_lista_lancamentos(client):
    await _cria_lancamento(client, descricao="MERCADO X")
    resp = await client.get("/lancamentos/tabela")
    assert resp.status_code == 200
    assert "MERCADO X" in resp.text


@pytest.mark.asyncio
async def test_tabela_fragmento_aplica_filtro_busca(client):
    await _cria_lancamento(client, descricao="MERCADO X")
    await _cria_lancamento(client, descricao="POSTO Y")
    resp = await client.get("/lancamentos/tabela", params={"busca": "posto"})
    assert "POSTO Y" in resp.text
    assert "MERCADO X" not in resp.text


@pytest.mark.asyncio
async def test_linha_fragmento_retorna_row(client):
    lanc = await _cria_lancamento(client, descricao="LINHA UNICA")
    resp = await client.get(f"/lancamentos/{lanc['id']}/linha")
    assert resp.status_code == 200
    assert f'id="row-{lanc["id"]}"' in resp.text
    assert "LINHA UNICA" in resp.text


@pytest.mark.asyncio
async def test_linha_fragmento_404_para_id_inexistente(client):
    resp = await client.get("/lancamentos/999999/linha")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_inline_update_categoria_confirma_e_gera_regra(client):
    lanc = await _cria_lancamento(client, descricao="POSTO SHELL INLINE")
    resp = await client.post(
        f"/lancamentos/inline-update/{lanc['id']}",
        data={"categoria": "TRANSPORTE", "subcategoria": "Combustivel"},
    )
    assert resp.status_code == 200
    assert "TRANSPORTE : Combustivel" in resp.text

    regras = (await client.get("/api/regras")).json()
    assert any(r["descricao"] == "POSTO SHELL INLINE" for r in regras)


@pytest.mark.asyncio
async def test_inline_update_valor_formato_br(client):
    lanc = await _cria_lancamento(client, descricao="VALOR BR")
    resp = await client.post(
        f"/lancamentos/inline-update/{lanc['id']}", data={"valor": "1.234,56"}
    )
    assert resp.status_code == 200
    detalhe = await client.get("/api/lancamentos")
    atualizado = next(x for x in detalhe.json() if x["id"] == lanc["id"])
    assert atualizado["valor"] == "1234.56"


@pytest.mark.asyncio
async def test_novo_lancamento_via_form(client):
    resp = await client.post(
        "/lancamentos/novo",
        data={
            "data": "2026-06-11",
            "descricao": "NOVO VIA FORM",
            "valor": "99.90",
            "tipo_valor": "saida",
            "categoria": "ALIMENTACAO",
            "subcategoria": "Delivery",
        },
    )
    assert resp.status_code == 200
    assert "NOVO VIA FORM" in resp.text
    assert resp.headers.get("hx-trigger") == "lancamentoCriado"


@pytest.mark.asyncio
async def test_batch_confirmar_via_form(client):
    a = await _cria_lancamento(client, descricao="A")
    b = await _cria_lancamento(client, descricao="B")
    resp = await client.post(
        "/lancamentos/batch-confirmar", data={"ids": [str(a["id"]), str(b["id"])]}
    )
    assert resp.status_code == 200
    lista = (await client.get("/api/lancamentos")).json()
    assert all(x["confirmado"] for x in lista)


@pytest.mark.asyncio
async def test_batch_excluir_via_form(client):
    a = await _cria_lancamento(client, descricao="EXCLUIR A")
    resp = await client.post("/lancamentos/batch-excluir", data={"ids": [str(a["id"])]})
    assert resp.status_code == 200
    assert "EXCLUIR A" not in resp.text
    assert (await client.get("/api/lancamentos")).json() == []

import pytest

CSV = (
    "data,descricao,valor\n"
    "2026-01-05,SUPERMERCADO,120.50\n"
    "2026-01-06,PAGAMENTO EFETUADO,-500.00\n"
    "2026-01-07,POSTO SHELL,80.00\n"
)

OFX = """<OFX><BANKTRANLIST>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20260105<TRNAMT>-50.00<FITID>FIT1<MEMO>MERCADO</STMTTRN>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20260110<TRNAMT>3000.00<FITID>FIT2<NAME>SALARIO</STMTTRN>
</BANKTRANLIST></OFX>"""


def _csv_file(conteudo=CSV, nome="fatura.csv"):
    return {"file": (nome, conteudo.encode("utf-8"), "text/csv")}


def _ofx_file(conteudo=OFX, nome="extrato.ofx"):
    return {"file": (nome, conteudo.encode("latin-1"), "application/x-ofx")}


@pytest.mark.asyncio
async def test_upload_csv_cria_lancamentos(client):
    resp = await client.post("/api/upload/csv", files=_csv_file())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_lidos"] == 2  # PAGAMENTO EFETUADO foi descartado
    assert body["novos"] == 2

    lancs = (await client.get("/api/lancamentos")).json()
    descricoes = {_l["descricao"] for _l in lancs}
    assert descricoes == {"SUPERMERCADO", "POSTO SHELL"}
    assert all(_l["fonte"] == "fatura" for _l in lancs)


@pytest.mark.asyncio
async def test_upload_csv_deduplica(client):
    await client.post("/api/upload/csv", files=_csv_file())
    resp = await client.post("/api/upload/csv", files=_csv_file())
    body = resp.json()
    assert body["novos"] == 0
    assert body["duplicados"] == 2
    assert len((await client.get("/api/lancamentos")).json()) == 2


@pytest.mark.asyncio
async def test_upload_csv_usa_regra_existente(client):
    await client.post(
        "/api/regras",
        json={"descricao": "POSTO SHELL", "categoria": "TRANSPORTE", "subcategoria": "Combustivel"},
    )
    resp = await client.post("/api/upload/csv", files=_csv_file())
    body = resp.json()
    posto = next(_l for _l in body["lancamentos"] if _l["descricao"] == "POSTO SHELL")
    assert posto["categoria"] == "TRANSPORTE"
    assert posto["origem"] == "regra_usuario"


@pytest.mark.asyncio
async def test_upload_ofx_credit_e_debit(client):
    resp = await client.post("/api/upload/ofx", files=_ofx_file())
    body = resp.json()
    assert body["novos"] == 2
    lancs = {_l["descricao"]: _l for _l in body["lancamentos"]}
    assert lancs["MERCADO"]["tipo_valor"] == "saida"
    assert lancs["SALARIO"]["tipo_valor"] == "entrada"
    assert all(_l["fonte"] == "extrato" for _l in body["lancamentos"])


@pytest.mark.asyncio
async def test_upload_ofx_deduplica_por_fitid(client):
    await client.post("/api/upload/ofx", files=_ofx_file())
    resp = await client.post("/api/upload/ofx", files=_ofx_file())
    body = resp.json()
    assert body["novos"] == 0
    assert body["duplicados"] == 2

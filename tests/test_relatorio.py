from src.services.relatorio import exibe_valor, montar_relatorio

CATEGORIAS = [
    {"nome": "ALIMENTACAO", "cor": "#8b5cf6", "tipo": "despesa"},
    {"nome": "SALARIO FRED", "cor": "#059669", "tipo": "receita"},
]

LANCS = [
    {"data": "2026-06-05", "descricao": "PADARIA", "valor": 100.0, "tipo_valor": "saida",
     "categoria": "ALIMENTACAO", "subcategoria": "Delivery"},
    {"data": "2026-06-10", "descricao": "MERCADO", "valor": 50.0, "tipo_valor": "saida",
     "categoria": "ALIMENTACAO", "subcategoria": "Supermercado"},
    {"data": "2026-06-20", "descricao": "SALARIO", "valor": 5000.0, "tipo_valor": "entrada",
     "categoria": "SALARIO FRED", "subcategoria": ""},
]


def test_exibe_valor_so_saida_vermelho():
    r = exibe_valor(100.0, 0.0)
    assert r["valor"] == 100.0 and r["cor"] == "var(--danger)"


def test_exibe_valor_so_entrada_verde():
    r = exibe_valor(0.0, 100.0)
    assert r["valor"] == 100.0 and r["cor"] == "var(--success)"


def test_exibe_valor_misto_cinza_liquido():
    r = exibe_valor(150.0, 50.0)
    assert r["valor"] == 100.0 and r["cor"] == "var(--muted)"


def test_montar_relatorio_vazio():
    assert montar_relatorio([], CATEGORIAS) == {"vazio": True}


def test_montar_relatorio_meses_e_totais():
    rel = montar_relatorio(LANCS, CATEGORIAS)
    assert rel["vazio"] is False
    assert rel["meses"] == ["2026-06"]
    assert rel["totais"]["saidas_geral"] == 150.0
    assert rel["totais"]["entradas_geral"] == 5000.0


def test_montar_relatorio_linhas_com_subcategorias():
    rel = montar_relatorio(LANCS, CATEGORIAS)
    alim = next(x for x in rel["linhas"] if x["categoria"] == "ALIMENTACAO")
    assert alim["total"]["valor"] == 150.0
    subnomes = {s["nome"] for s in alim["subs"]}
    assert subnomes == {"Delivery", "Supermercado"}


def test_montar_relatorio_chart_datasets():
    rel = montar_relatorio(LANCS, CATEGORIAS)
    labels = {d["label"] for d in rel["chart"]["datasets"]}
    assert labels == {"ALIMENTACAO", "SALARIO FRED"}

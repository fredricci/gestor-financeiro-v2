from src.services.consulta import build_cat_opcoes, filtrar_ordenar, meses_disponiveis

LANCS = [
    {"id": 1, "data": "2026-07-05", "descricao": "PADARIA CENTRAL", "valor": 32.90,
     "tipo_valor": "saida", "categoria": "ALIMENTACAO", "subcategoria": "Delivery",
     "origem": "ia", "confianca": "alta", "confirmado": False, "fonte": "fatura"},
    {"id": 2, "data": "2026-06-01", "descricao": "UBER TRIP", "valor": 25.30,
     "tipo_valor": "saida", "categoria": "TRANSPORTE", "subcategoria": "",
     "origem": "regra_usuario", "confianca": "alta", "confirmado": True, "fonte": "extrato"},
    {"id": 3, "data": "2026-06-15", "descricao": "SALARIO", "valor": 8500.0,
     "tipo_valor": "entrada", "categoria": "SALARIO FRED", "subcategoria": "",
     "origem": "confirmado", "confianca": "alta", "confirmado": True, "fonte": "manual"},
]


def test_filtro_origem_historico():
    r = filtrar_ordenar(LANCS, {"origem": "historico"})
    assert {x["id"] for x in r} == {2, 3}


def test_filtro_origem_alta_so_ia():
    r = filtrar_ordenar(LANCS, {"origem": "alta"})
    assert {x["id"] for x in r} == {1}


def test_filtro_fonte():
    r = filtrar_ordenar(LANCS, {"fonte": "extrato"})
    assert {x["id"] for x in r} == {2}


def test_filtro_mes():
    r = filtrar_ordenar(LANCS, {"mes": "2026-06"})
    assert {x["id"] for x in r} == {2, 3}


def test_busca_por_descricao_categoria_valor():
    assert {x["id"] for x in filtrar_ordenar(LANCS, {"busca": "uber"})} == {2}
    assert {x["id"] for x in filtrar_ordenar(LANCS, {"busca": "transporte"})} == {2}
    assert {x["id"] for x in filtrar_ordenar(LANCS, {"busca": "25,3"})} == {2}


def test_ordenacao_valor_desc_default():
    r = filtrar_ordenar(LANCS, {"ordem": "valor", "direcao": "desc"})
    assert [x["id"] for x in r] == [3, 1, 2]


def test_ordenacao_data_asc():
    r = filtrar_ordenar(LANCS, {"ordem": "data", "direcao": "asc"})
    assert [x["id"] for x in r] == [2, 3, 1]


def test_meses_disponiveis_ordenado_desc():
    assert meses_disponiveis(LANCS) == ["2026-07", "2026-06"]


def test_build_cat_opcoes_inclui_categoria_e_subcategorias():
    categorias = [
        {"nome": "ALIMENTACAO", "tipo": "despesa", "subcategorias": [{"nome": "Delivery"}]},
        {"nome": "SALARIO FRED", "tipo": "receita", "subcategorias": []},
    ]
    opcoes = build_cat_opcoes(categorias)
    assert {"cat": "ALIMENTACAO", "sub": "", "label": "ALIMENTACAO", "tipo": "despesa"} in opcoes
    esperado = {
        "cat": "ALIMENTACAO",
        "sub": "Delivery",
        "label": "ALIMENTACAO : Delivery",
        "tipo": "despesa",
    }
    assert esperado in opcoes
    assert len(opcoes) == 3

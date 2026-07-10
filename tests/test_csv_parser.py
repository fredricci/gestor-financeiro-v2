from decimal import Decimal

from src.services.csv_parser import parse_csv

HEADER = "data,descricao,valor\n"


def test_valor_positivo_eh_saida():
    linhas = parse_csv(HEADER + "2026-01-05,SUPERMERCADO,120.50")
    assert len(linhas) == 1
    assert linhas[0].tipo_valor == "saida"
    assert linhas[0].valor == Decimal("120.50")


def test_valor_negativo_eh_entrada_e_armazenado_absoluto():
    linhas = parse_csv(HEADER + "2026-01-06,ESTORNO,-30.00")
    assert linhas[0].tipo_valor == "entrada"
    assert linhas[0].valor == Decimal("30.00")


def test_ignora_pagamento_efetuado():
    conteudo = HEADER + "2026-01-07,PAGAMENTO EFETUADO,-500.00\n2026-01-08,PADARIA,15.00"
    linhas = parse_csv(conteudo)
    assert len(linhas) == 1
    assert linhas[0].descricao == "PADARIA"


def test_descricao_com_virgula_eh_preservada():
    linhas = parse_csv(HEADER + "2026-01-09,UBER, VIAGEM CENTRO,25.90")
    assert linhas[0].descricao == "UBER, VIAGEM CENTRO"
    assert linhas[0].valor == Decimal("25.90")


def test_ignora_linhas_vazias_e_malformadas():
    conteudo = HEADER + "\n2026-01-10,OK,10.00\n   \nlinha-invalida\n,,\n"
    linhas = parse_csv(conteudo)
    assert len(linhas) == 1
    assert linhas[0].descricao == "OK"


def test_csv_vazio_ou_so_header():
    assert parse_csv("") == []
    assert parse_csv("data,descricao,valor") == []

from decimal import Decimal

from src.services.ofx_parser import parse_ofx

OFX = """
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT<DTPOSTED>20260105120000<TRNAMT>-50.00<FITID>ABC123<MEMO>SUPERMERCADO VILA
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT<DTPOSTED>20260110<TRNAMT>2500.00<FITID>DEF456<NAME>SALARIO EMPRESA
</STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""


def test_debit_eh_saida():
    linhas = parse_ofx(OFX)
    saida = next(_l for _l in linhas if _l.fitid == "ABC123")
    assert saida.tipo_valor == "saida"
    assert saida.valor == Decimal("50.00")
    assert saida.data == "2026-01-05"
    assert saida.descricao == "SUPERMERCADO VILA"


def test_credit_eh_entrada():
    linhas = parse_ofx(OFX)
    entrada = next(_l for _l in linhas if _l.fitid == "DEF456")
    assert entrada.tipo_valor == "entrada"
    assert entrada.valor == Decimal("2500.00")
    assert entrada.descricao == "SALARIO EMPRESA"


def test_descricao_usa_name_quando_sem_memo():
    linhas = parse_ofx(OFX)
    entrada = next(_l for _l in linhas if _l.fitid == "DEF456")
    assert entrada.descricao == "SALARIO EMPRESA"


def test_ofx_sem_transacoes():
    assert parse_ofx("<OFX></OFX>") == []

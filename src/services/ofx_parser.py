"""Parser de extratos bancários em OFX.

Extrai cada bloco <STMTTRN>. Regras:
- <TRNTYPE>CREDIT = entrada; qualquer outro (DEBIT) = saída
- valor (<TRNAMT>) é sempre armazenado em módulo (positivo)
- descrição vem de <MEMO> ou, na ausência, <NAME>
- <FITID> é o identificador único do banco, usado para deduplicação
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_STMTTRN = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.IGNORECASE | re.DOTALL)


@dataclass
class LinhaOFX:
    data: str
    descricao: str
    valor: Decimal
    tipo_valor: str
    fitid: str


def _tag(bloco: str, tag: str) -> str:
    m = re.search(rf"<{tag}>([^\r\n<]+)", bloco, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_ofx(conteudo: str) -> list[LinhaOFX]:
    """Parseia o conteúdo de um OFX em linhas estruturadas."""
    resultado: list[LinhaOFX] = []

    for match in _STMTTRN.finditer(conteudo):
        bloco = match.group(1)

        dt_raw = _tag(bloco, "DTPOSTED")
        if len(dt_raw) < 8:
            continue
        data = f"{dt_raw[0:4]}-{dt_raw[4:6]}-{dt_raw[6:8]}"

        try:
            valor_num = Decimal(_tag(bloco, "TRNAMT"))
        except (InvalidOperation, ValueError):
            continue

        trntype = _tag(bloco, "TRNTYPE").upper()
        tipo_valor = "entrada" if trntype == "CREDIT" else "saida"

        descricao = _tag(bloco, "MEMO") or _tag(bloco, "NAME")
        if not descricao:
            continue

        resultado.append(
            LinhaOFX(
                data=data,
                descricao=descricao,
                valor=abs(valor_num),
                tipo_valor=tipo_valor,
                fitid=_tag(bloco, "FITID"),
            )
        )

    return resultado

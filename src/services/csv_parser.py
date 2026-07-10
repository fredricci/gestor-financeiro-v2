"""Parser de faturas de cartão em CSV.

Formato esperado (com linha de cabeçalho, ignorada):
    data,descricao,valor

Regras:
- valor positivo  = saída (despesa); valor negativo = entrada (estorno/pagamento)
- valor é sempre armazenado em módulo (positivo)
- linhas contendo "PAGAMENTO EFETUADO" na descrição são ignoradas
- a descrição pode conter vírgulas (campos do meio são reunidos)
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass
class LinhaCSV:
    data: str
    descricao: str
    valor: Decimal
    tipo_valor: str


def parse_csv(conteudo: str, arquivo: str = "") -> list[LinhaCSV]:
    """Parseia o conteúdo de um CSV de fatura em linhas estruturadas."""
    texto = conteudo.lstrip("﻿").strip()
    if not texto:
        return []

    linhas = texto.split("\n")[1:]  # pula o cabeçalho
    resultado: list[LinhaCSV] = []

    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        partes = linha.split(",")
        if len(partes) < 3:
            continue

        data = partes[0].strip()
        descricao = ",".join(partes[1:-1]).strip()
        valor_raw = partes[-1].strip()

        if not data or not descricao:
            continue
        if "PAGAMENTO EFETUADO" in descricao.upper():
            continue

        try:
            valor_num = Decimal(valor_raw)
        except (InvalidOperation, ValueError):
            continue

        tipo_valor = "saida" if valor_num >= 0 else "entrada"
        resultado.append(
            LinhaCSV(
                data=data,
                descricao=descricao,
                valor=abs(valor_num),
                tipo_valor=tipo_valor,
            )
        )

    return resultado

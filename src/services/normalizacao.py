"""Normalização de descrições para casamento de regras."""

import re

_PIX_SUFIXO_DATA = re.compile(r"\s+\d{2}\s+\d{2}$")


def normalizar(descricao: str) -> str:
    """Chave canônica de uma descrição: sem espaços nas pontas e em maiúsculas."""
    return descricao.strip().upper()


def normalizar_descricao(descricao: str) -> str:
    """Remove o sufixo de data 'DD MM' de lançamentos PIX.

    Ex: 'PIX PADARIA 03 08' -> 'PIX PADARIA'.
    """
    d = descricao.strip()
    if d.upper().startswith("PIX "):
        d = _PIX_SUFIXO_DATA.sub("", d).strip()
    return d


def chave_regra(descricao: str) -> str:
    """Chave normalizada usada para buscar/gravar regras."""
    return normalizar(normalizar_descricao(descricao))

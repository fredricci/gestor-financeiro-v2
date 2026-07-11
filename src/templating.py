"""Configuração do Jinja2: filtros, globais e helpers de apresentação."""

from datetime import date

from fastapi.templating import Jinja2Templates

# Ícone Lucide por categoria (nomes de ícones do lucide.dev).
CAT_ICONS = {
    "ALIMENTACAO": "shopping-cart",
    "BEBEL": "paw-print",
    "CAMILA": "user",
    "DESPESAS FIXAS": "calendar",
    "EXTRAS": "package",
    "FINANCEIRO": "landmark",
    "FRED": "user",
    "HABITACAO": "home",
    "IGNORADO": "eye-off",
    "LAZER": "music",
    "LUCA": "baby",
    "NAO LEMBRO": "help-circle",
    "SAUDE": "heart-pulse",
    "TRANSPORTE": "car",
    "SALARIO FRED": "wallet",
    "SALARIO CAMILA": "wallet",
    "REEMBOLSO": "arrow-down-circle",
    "RECEITA EXTRA": "trending-up",
}

COR_DESPESA = "#8b5cf6"
BG_DESPESA = "#f3e8ff"
COR_RECEITA = "#059669"
BG_RECEITA = "#d1fae5"
COR_NEUTRA = "#94a3b8"
BG_NEUTRA = "#f1f5f9"


def format_brl(value) -> str:
    """Formata número no padrão brasileiro: 100000.5 -> '100.000,50' (sem R$)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_data_br(value) -> str:
    """Converte data ISO (YYYY-MM-DD) ou date em 'dd/mm/aaaa'."""
    if value is None:
        return "—"
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    partes = str(value).split("-")
    if len(partes) != 3:
        return str(value)
    y, m, d = partes
    return f"{d}/{m}/{y}"


def cat_icon(nome: str) -> str:
    return CAT_ICONS.get(nome, "tag")


def cat_cores(nome: str, tipo: str | None = None) -> dict:
    """Retorna cor/bg do ícone conforme tipo (receita/despesa) ou nome conhecido."""
    if nome in ("IGNORADO", "NAO LEMBRO"):
        return {"cor": COR_NEUTRA, "bg": BG_NEUTRA}
    is_receita = tipo == "receita" or nome in (
        "SALARIO FRED",
        "SALARIO CAMILA",
        "REEMBOLSO",
        "RECEITA EXTRA",
    )
    if is_receita:
        return {"cor": COR_RECEITA, "bg": BG_RECEITA}
    return {"cor": COR_DESPESA, "bg": BG_DESPESA}


def mes_label(mes: str) -> str:
    """'2026-01' -> '01/2026'."""
    if not mes or "-" not in mes:
        return mes
    y, m = mes.split("-")[:2]
    return f"{m}/{y}"


templates = Jinja2Templates(directory="templates")
templates.env.filters["brl"] = format_brl
templates.env.filters["data_br"] = format_data_br
templates.env.filters["mes_label"] = mes_label
templates.env.globals["cat_icon"] = cat_icon
templates.env.globals["cat_cores"] = cat_cores
templates.env.globals["mes_label"] = mes_label

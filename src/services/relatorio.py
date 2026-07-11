"""Cálculo server-side do relatório (gráfico + resumo por categoria/mês).

Porta a lógica que antes vivia no frontend: valores líquidos por categoria/mês,
datasets do gráfico de barras empilhadas e a tabela de resumo com detalhamento.
"""

from src.templating import BG_NEUTRA, COR_NEUTRA, cat_cores, cat_icon


def _soma(lancs: list[dict], tipo: str) -> float:
    return sum(x["valor"] for x in lancs if x["tipo_valor"] == tipo)


def exibe_valor(saidas: float, entradas: float) -> dict:
    """Valor líquido absoluto e cor: só entradas=verde, só saídas=vermelho, misto=cinza."""
    if saidas == 0:
        val, cor = entradas, "var(--success)"
    elif entradas == 0:
        val, cor = saidas, "var(--danger)"
    else:
        val, cor = saidas - entradas, "var(--muted)"
    return {"valor": abs(val), "cor": cor}


def montar_relatorio(lancamentos: list[dict], categorias: list[dict]) -> dict:
    """Estrutura completa do relatório para os templates."""
    if not lancamentos:
        return {"vazio": True}

    cor_por_cat = {c["nome"]: c["cor"] for c in categorias}
    tipo_por_cat = {c["nome"]: c["tipo"] for c in categorias}

    meses = sorted({str(x["data"])[:7] for x in lancamentos})
    cats = list(dict.fromkeys(x["categoria"] for x in lancamentos))

    def no_mes(lancs: list[dict], mes: str) -> list[dict]:
        return [x for x in lancs if str(x["data"])[:7] == mes]

    def liquido(lancs: list[dict], mes: str) -> float:
        no = no_mes(lancs, mes)
        return _soma(no, "saida") - _soma(no, "entrada")

    # ── Cards de saldo por mês ──
    saldo_por_mes = []
    for mes in meses:
        no = no_mes(lancamentos, mes)
        ent = _soma(no, "entrada")
        sai = _soma(no, "saida")
        saldo_por_mes.append(
            {"mes": mes, "entradas": ent, "saidas": sai, "saldo": ent - sai}
        )

    # ── Datasets do gráfico (ordenados asc pelo total positivo → maiores no topo) ──
    def total_positivo(cat: str) -> float:
        lancs = [x for x in lancamentos if x["categoria"] == cat]
        return sum(max(0.0, liquido(lancs, m)) for m in meses)

    cats_chart = sorted(cats, key=total_positivo)
    datasets = []
    for cat in cats_chart:
        lancs = [x for x in lancamentos if x["categoria"] == cat]
        datasets.append(
            {
                "label": cat,
                "data": [max(0.0, liquido(lancs, m)) for m in meses],
                "cor": cor_por_cat.get(cat, COR_NEUTRA),
            }
        )

    # ── Tabela de resumo (ordenada desc pelo total positivo) ──
    cats_resumo = sorted(cats, key=total_positivo, reverse=True)
    linhas = []
    for cat in cats_resumo:
        lancs = [x for x in lancamentos if x["categoria"] == cat]
        if not lancs:
            continue
        cores = cat_cores(cat, tipo_por_cat.get(cat))
        cols = []
        for mes in meses:
            no = no_mes(lancs, mes)
            if not no:
                cols.append(None)
            else:
                cols.append(exibe_valor(_soma(no, "saida"), _soma(no, "entrada")))
        total = exibe_valor(_soma(lancs, "saida"), _soma(lancs, "entrada"))

        subnomes = list(dict.fromkeys(x["subcategoria"] or "—" for x in lancs))

        def _tot_sub(nome: str, _lancs=lancs) -> float:
            sub = [x for x in _lancs if (x["subcategoria"] or "—") == nome]
            return _soma(sub, "saida") - _soma(sub, "entrada")

        subnomes.sort(key=_tot_sub, reverse=True)
        subs = []
        for sub in subnomes:
            slancs = [x for x in lancs if (x["subcategoria"] or "—") == sub]
            scols = []
            for mes in meses:
                no = no_mes(slancs, mes)
                scols.append(
                    exibe_valor(_soma(no, "saida"), _soma(no, "entrada")) if no else None
                )
            subs.append(
                {
                    "nome": sub,
                    "cols": scols,
                    "total": exibe_valor(_soma(slancs, "saida"), _soma(slancs, "entrada")),
                }
            )

        linhas.append(
            {
                "categoria": cat,
                "cor": cores["cor"],
                "bg": cores["bg"],
                "icon": cat_icon(cat),
                "cols": cols,
                "total": total,
                "subs": subs,
            }
        )

    # ── Linhas de totais ──
    tot_saidas_mes = [_soma(no_mes(lancamentos, m), "saida") for m in meses]
    tot_entradas_mes = [_soma(no_mes(lancamentos, m), "entrada") for m in meses]

    return {
        "vazio": False,
        "meses": meses,
        "saldo_por_mes": saldo_por_mes,
        "chart": {"labels": meses, "datasets": datasets},
        "linhas": linhas,
        "totais": {
            "saidas_mes": tot_saidas_mes,
            "entradas_mes": tot_entradas_mes,
            "saidas_geral": _soma(lancamentos, "saida"),
            "entradas_geral": _soma(lancamentos, "entrada"),
        },
        "cor_neutra": COR_NEUTRA,
        "bg_neutra": BG_NEUTRA,
    }

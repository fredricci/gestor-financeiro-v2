"""Construção do prompt e parsing da resposta da IA de categorização.

Funções puras (sem I/O) — testáveis isoladamente.
"""

import json

from src.services.normalizacao import normalizar_descricao

# Taxonomia completa (despesas + receitas) apresentada à IA.
CATEGORIAS = """DESPESAS:
- ALIMENTACAO: Delivery; Refeições; Supermercado, padaria, feira
- BEBEL (pet): Racao, Banho, Tosa, Vet
- CAMILA: Roupas e acessórios; Cuidados pessoais (salão, estética)
- DESPESAS FIXAS: Bebel-creche; Camila-Academia; Fred-Ingles; Habitacao-Aluguel;
  Habitacao-Celular e Internet; Habitacao-Condominio; Habitacao-Empregada;
  Habitacao-Empregada (impostos); Habitacao-Gas
- EXTRAS: compras diversas (Amazon, Mercado Livre)
- FINANCEIRO: tarifas bancárias, tag de pedágio, juros
- FRED: Almoço; Cuidados Pessoais/academia; Roupas e Acessorios (fred)
- HABITACAO: Manutencao, Serviços Gerais
- IGNORADO: transferências internas, desconsiderar
- LAZER: Apps; Bares, Restaurantes, Eventos; Jogos de Futebol; Presentes; Viagens; Clube Ipe
- LUCA (filho): Presentes e Brinquedos; Roupas e Acessorios (luca)
- NAO LEMBRO: não identificado
- SAUDE: Farmacia; Médicos; Suplementos
- TRANSPORTE: Combustivel; Estacionamento; Lavagem; Manutencao; Sem parar; Uber, Taxi, Metro

RECEITAS:
- SALARIO FRED: salário recebido pelo Fred
- SALARIO CAMILA: salário recebido pela Camila
- REEMBOLSO: reembolsos recebidos (DEV PIX, estornos)
- RECEITA EXTRA: demais entradas"""

# Regras heurísticas gerais (histórico do usuário tem prioridade sobre estas).
REGRAS_BASE = """- CARE CLUB, CROSSFIT, LEV ITAIM = FRED / Cuidados Pessoais/academia
- Uber, 99APP, DL*99 RIDE = TRANSPORTE / Uber, Taxi, Metro
- CANTINAS ESCOLARES CAL = DESPESAS FIXAS / Bebel-creche
- VILA ZAIRA, OBA HORTIFRUTI, supermercados = ALIMENTACAO / Supermercado, padaria, feira
- IFD*, IFOOD = ALIMENTACAO / Delivery
- AMAZON BR, AMAZONMKTPLC, MERCADOLIVRE = EXTRAS
- APPLECOMBILL, Netflix, Spotify, Disney, Google One, Amazon Prime =
  DESPESAS FIXAS / Habitacao-Celular e Internet
- CLUB ATHLETICO PAULIST, AVANTI PALMEIRAS, ZIG*ALLIANZ = LAZER / Jogos de Futebol
- RAIA, DROGARIA, NOSSA SAUDE, RDSAUDE = SAUDE / Farmacia
- Posto de gasolina = TRANSPORTE / Combustivel
- VG PARK, SUZUKI E ARAUJO LOCA, ESTACIONAMENTO = TRANSPORTE / Estacionamento
- COBASI, pet shop = BEBEL / Racao, Banho, Tosa, Vet
- MICROSOFT*XBOX, M3 GESTAO ESPORTIVA = LUCA
- TagItau = FINANCEIRO
- TED/PIX recebido de valor alto = SALARIO FRED ou SALARIO CAMILA
- DEV PIX, reembolso recebido = REEMBOLSO"""


def construir_prompt(itens: list[dict], historico: list[tuple[str, str, str]]) -> str:
    """Monta o prompt de categorização em lote.

    itens: lista de dicts com 'descricao', 'valor' e 'tipo_valor'.
    historico: lista de (descricao, categoria, subcategoria) já confirmados.
    """
    lista = "\n".join(
        f"{i + 1}. {normalizar_descricao(it['descricao'])} | "
        f"R$ {it.get('valor', '') or ''} | {it.get('tipo_valor', 'saida')}"
        for i, it in enumerate(itens)
    )

    historico_texto = ""
    if historico:
        linhas = "\n".join(
            f"- {desc} -> {cat}{(' / ' + sub) if sub else ''}"
            for desc, cat, sub in historico
        )
        historico_texto = (
            "\n\nHISTÓRICO CONFIRMADO PELO USUÁRIO "
            "(referência PRINCIPAL — use quando a descrição for parecida):\n" + linhas
        )

    return f"""Você categoriza lançamentos financeiros de uma família brasileira.
Responda APENAS com um array JSON válido, sem texto antes ou depois.

CATEGORIAS DISPONÍVEIS:
{CATEGORIAS}

REGRAS GERAIS:
{REGRAS_BASE}{historico_texto}

INSTRUÇÕES:
- Priorize SEMPRE o histórico confirmado pelo usuário sobre as regras gerais.
- Se a descrição for parecida com algo do histórico, use a mesma categoria/subcategoria.
- Respeite o tipo_valor informado (entrada = receita, saida = despesa).
- confianca: "alta" quando tiver certeza, "media" quando provável, "baixa" quando incerto.
- Desconhecidos: categoria "NAO LEMBRO", confianca "baixa".
- subcategoria pode ser string vazia quando não se aplicar.

LANÇAMENTOS (mantenha a ordem e a quantidade):
{lista}

Formato (um objeto por lançamento, mesma ordem):
[{{"descricao":"...","categoria":"CATEGORIA","subcategoria":"...","confianca":"alta|media|baixa"}}]"""


def parse_resposta_ia(texto: str, itens: list[dict]) -> list[dict]:
    """Converte a resposta textual da IA em resultados alinhados aos itens.

    Levanta ValueError se o JSON for inválido ou a contagem não bater.
    """
    limpo = texto.replace("```json", "").replace("```", "").strip()
    dados = json.loads(limpo)
    if not isinstance(dados, list):
        raise ValueError("resposta da IA não é uma lista")
    if len(dados) != len(itens):
        raise ValueError(
            f"IA retornou {len(dados)} itens, esperados {len(itens)}"
        )

    resultados: list[dict] = []
    for item, cat in zip(itens, dados, strict=True):
        resultados.append(
            {
                "descricao": item["descricao"],
                "categoria": cat.get("categoria", "NAO LEMBRO"),
                "subcategoria": cat.get("subcategoria", "") or "",
                "confianca": cat.get("confianca", "baixa"),
                "origem": "ia",
                "tipo_valor": item.get("tipo_valor", "saida"),
            }
        )
    return resultados

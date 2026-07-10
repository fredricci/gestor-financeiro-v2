"""Popula as categorias e subcategorias iniciais. Idempotente — seguro rodar mais de uma vez.

Uso:
    python -m src.seed
"""

import asyncio

from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.models import Categoria, Subcategoria

COR_DESPESA = "#8b5cf6"
COR_RECEITA = "#059669"

CATEGORIAS_DESPESA = [
    "ALIMENTACAO",
    "BEBEL",
    "CAMILA",
    "DESPESAS FIXAS",
    "EXTRAS",
    "FINANCEIRO",
    "FRED",
    "HABITACAO",
    "IGNORADO",
    "LAZER",
    "LUCA",
    "NAO LEMBRO",
    "SAUDE",
    "TRANSPORTE",
]

CATEGORIAS_RECEITA = [
    "SALARIO FRED",
    "SALARIO CAMILA",
    "REEMBOLSO",
    "RECEITA EXTRA",
]

SUBCATEGORIAS = {
    "ALIMENTACAO": ["Delivery", "Refeições", "Supermercado padaria feira"],
    "BEBEL": ["Racao Banho Tosa Vet"],
    "CAMILA": ["Roupas e acessorios", "Cuidados pessoais"],
    "DESPESAS FIXAS": [
        "Bebel-creche",
        "Camila-Academia",
        "Fred-Ingles",
        "Habitacao-Aluguel",
        "Habitacao-Celular e Internet",
        "Habitacao-Condominio",
        "Habitacao-Empregada",
        "Habitacao-Empregada (impostos)",
        "Habitacao-Gas",
    ],
    "FRED": ["Almoço", "Cuidados Pessoais/academia", "Roupas e Acessorios (fred)"],
    "HABITACAO": ["Manutencao Serviços Gerais"],
    "LAZER": [
        "Apps",
        "Bares Restaurantes Eventos",
        "Jogos de Futebol",
        "Presentes",
        "Viagens",
        "Clube Ipe",
    ],
    "LUCA": ["Presentes e Brinquedos", "Roupas e Acessorios (luca)"],
    "SAUDE": ["Farmacia", "Médicos", "Suplementos"],
    "TRANSPORTE": [
        "Combustivel",
        "Estacionamento",
        "Lavagem",
        "Manutencao",
        "Sem parar",
        "Uber Taxi Metro",
    ],
}


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        categorias_por_nome: dict[str, Categoria] = {}

        for nome in CATEGORIAS_DESPESA + CATEGORIAS_RECEITA:
            existente = (
                await session.execute(select(Categoria).where(Categoria.nome == nome))
            ).scalar_one_or_none()
            if existente:
                categorias_por_nome[nome] = existente
                continue
            tipo = "despesa" if nome in CATEGORIAS_DESPESA else "receita"
            cor = COR_DESPESA if tipo == "despesa" else COR_RECEITA
            categoria = Categoria(nome=nome, cor=cor, tipo=tipo)
            session.add(categoria)
            await session.flush()
            categorias_por_nome[nome] = categoria
            print(f"  + categoria {nome} ({tipo})")

        for cat_nome, subnomes in SUBCATEGORIAS.items():
            categoria = categorias_por_nome[cat_nome]
            for sub_nome in subnomes:
                existente = (
                    await session.execute(
                        select(Subcategoria).where(
                            Subcategoria.categoria_id == categoria.id,
                            Subcategoria.nome == sub_nome,
                        )
                    )
                ).scalar_one_or_none()
                if existente:
                    continue
                session.add(Subcategoria(categoria_id=categoria.id, nome=sub_nome))
                print(f"    - subcategoria {cat_nome} / {sub_nome}")

        await session.commit()
    print("Seed concluído.")


if __name__ == "__main__":
    asyncio.run(seed())

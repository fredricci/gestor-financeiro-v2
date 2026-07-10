#!/usr/bin/env bash
# Sobe o Postgres (Docker), aplica migrations e popula categorias.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado nesta máquina."
    echo "Use um Postgres já disponível: ajuste DATABASE_URL no .env e rode:"
    echo "  alembic upgrade head && python -m src.seed"
    exit 1
fi

docker compose up -d postgres

echo "Aguardando Postgres ficar saudável..."
until docker compose exec -T postgres pg_isready -U gestor -d gestor_financeiro > /dev/null 2>&1; do
    sleep 1
done

alembic upgrade head
python -m src.seed

echo "Pronto: schema aplicado e categorias seedadas."

# Gestor Financeiro (v2)

Reescrita do gestor financeiro pessoal/familiar com stack profissional: FastAPI + SQLAlchemy 2.x async + Alembic + PostgreSQL 16. Substitui o protótipo em `~/gestor-financeiro` (não modificado por este projeto).

## Stack (Fase 1)

- Python 3.12+, FastAPI, SQLAlchemy 2.x (async), Alembic, PostgreSQL 16
- asyncpg (runtime) + psycopg2 (Alembic)
- Pydantic v2 / pydantic-settings
- pip + venv (sem uv/poetry, mesmo padrão do projeto `orcamento-obra`)

## Estrutura

```
gestor-financeiro-v2/
├── src/
│   ├── config.py       # Settings (pydantic-settings, lê .env)
│   ├── database.py     # engine + sessão async do SQLAlchemy
│   ├── models/          # Categoria, Subcategoria, Lancamento, Regra
│   └── seed.py          # popula categorias/subcategorias iniciais (idempotente)
├── migrations/          # Alembic (autogenerate a partir dos models)
├── scripts/setup.sh     # sobe Postgres via Docker + migrations + seed
├── docker-compose.yml   # Postgres 16 local
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## ⚠️ Nota sobre este ambiente

Nesta máquina **Docker não está instalado** ainda. O `docker-compose.yml` está pronto para quando você instalar o Docker Desktop, mas a Fase 1 foi validada usando o **PostgreSQL nativo** que já roda na porta 5432 (o mesmo que serve o `gestor_financeiro` do projeto antigo).

Para isolar do banco de produção do projeto antigo, foram criados nesse Postgres nativo:
- role `gestor` / senha `gestor`
- banco `gestor_financeiro_v2` (owned by `gestor`) — **não é o banco `gestor_financeiro` antigo**, que continua intocado

O `.env` local do projeto (gitignorado) já aponta para esse banco de desenvolvimento. Quando o Docker estiver instalado, troque o `DATABASE_URL` para o valor de `.env.example` (banco `gestor_financeiro` dentro do container).

## Como rodar

### Com Docker (quando disponível)

```bash
cp .env.example .env
# edite .env se necessário

docker compose up -d postgres
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head
python -m src.seed
```

Ou simplesmente: `./scripts/setup.sh` (assume venv já ativado e dependências instaladas).

### Sem Docker (usado para validar esta Fase 1 hoje)

```bash
source venv/bin/activate   # venv já criado e com deps instaladas
alembic upgrade head        # aplica o schema em gestor_financeiro_v2
python -m src.seed          # popula as 18 categorias e subcategorias
```

### Conferir os dados

```bash
psql -U gestor -d gestor_financeiro_v2 -h localhost -c "SELECT nome, tipo, cor FROM categorias ORDER BY tipo, nome;"
psql -U gestor -d gestor_financeiro_v2 -h localhost -c "SELECT c.nome, s.nome FROM subcategorias s JOIN categorias c ON c.id = s.categoria_id ORDER BY c.nome, s.nome;"
```

## Modelos

- **Categoria**: `id, nome, cor, tipo (despesa|receita), criado_em`
- **Subcategoria**: `id, categoria_id (FK), nome, criado_em`
- **Lancamento**: `id, data, descricao, valor, tipo_valor, categoria, subcategoria, origem, confianca, confirmado, arquivo, fitid, criado_em`
- **Regra**: `descricao (PK), categoria, subcategoria, atualizado_em`

`categoria`/`subcategoria` em `Lancamento` são texto livre (não FK) — mesma decisão do protótipo antigo, para desacoplar o histórico de lançamentos de mudanças na taxonomia.

## Próxima fase

Fase 2 só começa após aprovação.

# Decisions

## Core Decisions

1. Use a monorepo so backend, ML, SQL, BI, and frontend work can evolve together with shared tooling.
2. Keep raw CSV files on the filesystem and only store cleaned/curated layers in PostgreSQL.
3. Separate `backend` and `ml-api` so inference contracts can evolve independently from product APIs.
4. Use Docker Compose for local orchestration because the goal is fast team onboarding, not deployment maturity.
5. Restrict Alembic to foundational DDL; analytical SQL belongs in `sql/`.
6. Keep `libs/common` small and explicit to avoid accidental framework-building.

## Deferred Decisions

- Final data quality rules for `data.csv` and `events.csv`
- Feature store strategy, if any, beyond SQL-defined feature tables
- Model registry behavior beyond the placeholder `serving.model_registry`
- BI asset versioning and promotion workflow
- Auth and role design for the MVP application

## Working Rule

When adding real implementation, prefer boring explicit modules, documented contracts, and narrow ownership over convenience abstractions.

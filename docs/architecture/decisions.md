# Decisions

## ADR-001: Raw CSV stays on the filesystem

- Context: `data.csv` and `events.csv` are source files, not warehouse-ready relational tables.
- Decision: keep raw files mounted under `data/raw/` and let ETL own parsing, encoding cleanup, and normalization.
- Consequence: PostgreSQL starts at `clean`, not at a raw-ingest replica layer.

## ADR-002: Alembic is limited to foundational DDL

- Context: the project needs reproducible schemas, technical tables, and indexes without mixing analytical logic into migrations.
- Decision: Alembic owns schema creation, technical tables, foundational DDL, indexes, and foundational grants only.
- Consequence: migrations stay stable and operational, while business SQL evolves separately.

## ADR-003: SQL files own marts, features, and serving refresh logic

- Context: analytical logic changes faster than foundational database structure and is easier to review as SQL artifacts.
- Decision: keep marts, features, and serving definitions in `sql/clean`, `sql/mart`, `sql/feature`, and `sql/serving`.
- Consequence: data engineers can work on refresh logic without expanding Alembic scope.

## ADR-004: Backend and ml-api are separate services

- Context: product-facing APIs and model-serving contracts evolve at different rates and should remain independently replaceable.
- Decision: keep `apps/backend` and `apps/ml_api` as separate FastAPI services.
- Consequence: backend owns orchestration, while ml-api owns inference contracts and future artifact loading.

## Working Rule

Prefer explicit modules, narrow ownership, and documented TODOs over convenience abstractions.

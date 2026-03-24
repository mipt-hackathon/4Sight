# Retail Analytics Hackathon Monorepo

This repository is the initial scaffold for a retail analytics application that will later combine churn prediction, recommendations, retail analytics, dashboards, and an MVP web app. It is intentionally limited to runnable infrastructure, service boundaries, developer workflows, SQL placeholders, and stubbed entrypoints.

## Already Scaffolded

- `apps/backend`: FastAPI app-facing API with stub routes
- `apps/ml_api`: separate FastAPI ML interface with stub prediction contracts
- `apps/frontend`: Next.js placeholder UI shell
- `jobs/*`: ETL, mart refresh, feature refresh, training, and batch scoring CLIs
- `sql/*`: placeholders for clean, mart, feature, and serving logic
- `infra/postgres/init`: bootstrap-only PostgreSQL init scripts
- `apps/backend/alembic`: single source of truth for schema creation and foundational DDL
- `infra/superset`: local Superset image/config scaffold
- `libs/common`: shared config, logging, DB, metrics, and utility helpers
- `tests`: lightweight boot and health endpoint tests

## Intentionally Stubbed

- No cleaning, deduplication, or business transformations yet
- No real marts, features, or serving SQL
- No trained models or inference logic
- No auth system
- No dashboard definitions
- No fake analytical outputs
- No raw CSV replica tables inside PostgreSQL

## Data Assumptions

- `data/raw/data.csv` is expected to be a wide denormalized transactional dataset
- `data/raw/events.csv` is expected to be a behavioral event log
- `events.csv` can contain missing `user_id` values
- encoding cleanup may be required during ETL
- customer identity resolution is a later implementation task
- the intended warehouse lifecycle is `clean -> mart -> feature -> serving`

Raw CSVs stay on the filesystem and are parsed by ETL jobs. The current ETL implementation loads directly into typed clean tables:

- `data.csv` -> `clean.users`, `clean.orders`, `clean.order_items`
- `events.csv` -> `clean.events`

What is already handled:
- structural split by entity
- typed columns for IDs, timestamps, numerics, booleans, UUIDs, and coordinates
- safe deduplication for `users`, `orders`, and `order_items` where the raw file repeats identical entity rows

What is still intentionally deferred:
- business cleaning rules
- null-handling policies beyond empty-string to `NULL`
- customer identity resolution
- event deduplication or reconciliation

## Top-Level Ownership

- `apps/`: application services
- `jobs/`: batch and offline workflows
- `sql/`: analytical SQL owned outside Alembic
- `infra/`: local infrastructure bootstrap
- `libs/`: shared code
- `docs/`: architecture and decision notes
- `data/`: mounted local input files
- `artifacts/`: model artifacts and future exports

## Startup Sequence

1. Bootstrap core infra and foundational DDL:

   ```bash
   make bootstrap
   ```

   This will:

   - copy `.env.example` to `.env` if needed
   - start `postgres` and `redis`
   - run `alembic upgrade head` inside the backend container

2. Start the long-running local stack:

   ```bash
   make up
   ```

3. Open local services:

- Frontend: [http://localhost:13000](http://localhost:13000)
- Backend docs: [http://localhost:18000/docs](http://localhost:18000/docs)
- ML API docs: [http://localhost:18001/docs](http://localhost:18001/docs)
- Superset: [http://localhost:18088](http://localhost:18088)

## Migration Flow

- `make migrate`: apply foundational Alembic migrations
- `make current`: print the current Alembic revision
- `make reset-db`: drop local volumes, restart `postgres` and `redis`, then rerun migrations

Alembic owns:

- schema creation
- technical tables
- foundational DDL
- indexes
- foundational grants tied to those schemas

Alembic does not own marts, features, or serving SQL transformations. Those stay in `sql/`.

## Developer Workflow

- `make backend-shell`: open a shell in the backend container
- `make ml-shell`: open a shell in the ml-api container
- `make db-shell`: open a shell in the postgres container
- `make psql`: open `psql` inside the postgres container
- `make etl`: run the ETL scaffold CLI
- `make marts`: run the mart refresh scaffold CLI
- `make features`: run the feature refresh scaffold CLI
- `make train`: run the training scaffold CLI
- `make score`: run the batch scoring scaffold CLI
- `make pipeline`: run ETL, marts, features, train, and batch scoring in sequence
- `make test`: run lightweight tests
- `make lint`: run Ruff checks
- `make format`: run Ruff formatting

## Service Responsibilities

- Backend: product-facing APIs and future orchestration over curated/serving data
- ML API: inference contracts and future model-serving behavior
- Jobs: filesystem ingestion, SQL refreshes, model training, and batch scoring
- Current ETL demo: load `data/raw/*.csv` directly into typed `clean.*` tables
- Superset: separate metadata DB plus a dedicated read-only analytics connection into `mart` and `serving`
- Frontend: placeholder MVP surface for dashboard, customer, churn, recommendations, and forecast views

For the scaffold, Superset metadata lives in a separate PostgreSQL database, while dashboard datasets should be registered against the BI read-only DSN and limited to `mart` and `serving`.

## Parallel Team Split

- Backend engineers: `apps/backend/`
- ML engineers: `apps/ml_api/`, `jobs/train/`, `jobs/batch_scoring/`
- Data engineers: `jobs/etl/`, `jobs/marts_builder/`, `jobs/feature_builder/`, `sql/`
- BI engineers: `infra/superset/`, future Superset assets, and mart/serving consumption
- Frontend engineers: `apps/frontend/`

## Working Rules

- Prefer explicit modules and TODOs over abstraction
- Keep raw CSVs on disk
- Keep Alembic disciplined and limited to foundational DDL
- Keep analytical SQL in `sql/`
- Use `mart` and `serving` as the default read surfaces for BI and application consumers

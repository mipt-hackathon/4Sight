# Retail Analytics Hackathon Monorepo

This repository is the initial engineering scaffold for a retail analytics hackathon project. It is intentionally limited to infrastructure, service boundaries, developer tooling, and placeholder modules so multiple team members can start working in parallel without stepping on each other.

The product scope this scaffold is designed to support later:

- churn prediction
- recommendation engine
- retail sales analytics
- interactive dashboards / BI
- MVP web application

## What This Repository Contains

- A FastAPI backend for product-facing APIs and orchestration.
- A separate FastAPI `ml-api` for model-serving contracts and inference stubs.
- Job packages for ETL, marts, features, training, and batch scoring.
- SQL folders for clean, mart, feature, and serving refresh logic.
- PostgreSQL, Redis, pgAdmin, and Apache Superset via Docker Compose.
- Shared Python utilities under `libs/common`.
- Base Alembic migration setup for foundational DDL only.
- A minimal Next.js frontend placeholder with route shells.

## What Is Intentionally Not Implemented Yet

- No real ML models or training pipelines.
- No real ETL parsing, validation, or loading logic.
- No actual marts, features, or serving SQL transformations.
- No production auth implementation.
- No finished BI dashboards.
- No Kubernetes, cloud deployment, or environment-specific delivery pipelines.
- No raw CSV ingestion into PostgreSQL raw tables.

## Architecture Overview

The repository is organized around clear ownership boundaries:

- `apps/backend`: application-facing API, orchestration, and aggregation layer.
- `apps/ml_api`: model-serving interface layer with placeholder prediction contracts.
- `apps/frontend`: MVP web application placeholder.
- `jobs/*`: asynchronous and batch-oriented processing entrypoints.
- `sql/*`: SQL owned by data and analytics workflows, separated by warehouse layer.
- `infra/*`: local infrastructure bootstrap and service configuration.
- `libs/common`: shared Python utilities for config, logging, DB access, metrics, and small helpers.

Raw files such as `data.csv` and `events.csv` are expected to be mounted from the filesystem into `data/raw/`. They are not modeled as raw PostgreSQL tables. PostgreSQL is reserved for cleaned, curated, mart, feature, and serving layers.

## Repository Structure

```text
apps/
  backend/        FastAPI backend API
  ml_api/         FastAPI ML serving API
  frontend/       Next.js placeholder frontend
jobs/
  etl/            Filesystem-to-database ingestion scaffold
  marts_builder/  Mart refresh job scaffold
  feature_builder/ Feature refresh job scaffold
  train/          Model training scaffold
  batch_scoring/  Batch scoring scaffold
sql/
  clean/          Clean-layer SQL placeholders
  mart/           Mart-layer SQL placeholders
  feature/        Feature-layer SQL placeholders
  serving/        Serving-layer SQL placeholders
infra/
  postgres/init/  Database bootstrap SQL
  superset/       Superset image and config
libs/common/      Shared Python utilities
docs/architecture/ Architecture and design notes
artifacts/models/ Placeholder model artifact directory
data/raw/         Mounted CSV input location
tests/            Basic boot and health checks
notebooks/        Scratch analysis notebooks
```

## Service Responsibilities

### Backend

- Exposes app-facing endpoints under `/api/...`
- Owns request composition and future domain orchestration
- Reads curated/serving data from PostgreSQL
- Delegates inference requests to `ml-api` when that integration is implemented

### ML API

- Exposes model-serving endpoints under `/ml/...`
- Defines placeholder request/response contracts for churn, recommendations, forecasting, and segmentation
- Will later load model artifacts from `artifacts/models/`

### Jobs

- `etl`: parse mounted CSVs, validate them, and load curated tables
- `marts_builder`: refresh mart-layer SQL
- `feature_builder`: refresh feature-layer SQL
- `train`: train and register model artifacts
- `batch_scoring`: write serving outputs from trained models

### BI

- Apache Superset is included as the BI layer
- BI should consume PostgreSQL curated, mart, feature, and serving outputs
- Dashboard definitions are intentionally not created yet

## Local Startup

1. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

2. Start the main stack:

   ```bash
   make up
   ```

3. Open local services:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ML API docs: [http://localhost:8001/docs](http://localhost:8001/docs)
- Superset: [http://localhost:8088](http://localhost:8088)
- pgAdmin: [http://localhost:5050](http://localhost:5050)

4. Run foundational migrations after services are healthy:

   ```bash
   docker compose --env-file .env exec backend alembic upgrade head
   ```

## Developer Workflow

- `make up`: start infra and long-running application services
- `make down`: stop everything
- `make etl`: run the ETL scaffold container
- `make marts`: run mart refresh scaffold
- `make features`: run feature refresh scaffold
- `make train`: run model training scaffold
- `make score`: run batch scoring scaffold
- `make pipeline`: run all batch steps in sequence
- `make test`: run placeholder tests
- `make lint`: run Ruff checks
- `make format`: run Ruff formatter
- `make reset-db`: destroy local DB volumes and recreate Postgres/Redis

## Conventions

- Keep application APIs, ML APIs, jobs, SQL, and BI assets in separate folders.
- Use PostgreSQL schemas `clean`, `mart`, `feature`, and `serving`.
- Keep Alembic limited to foundational DDL, schema creation, base tables, and technical indexes.
- Put business SQL in `sql/`, not in Alembic migrations.
- Treat `libs/common` as a small shared toolbox, not a framework.
- Use explicit TODO markers when a stub is ready for implementation.
- Do not load raw CSVs into PostgreSQL as raw replica tables.

## Parallel Team Ownership Suggestions

- Backend engineers work in `apps/backend/`
- ML engineers work in `apps/ml_api/`, `jobs/train/`, and `jobs/batch_scoring/`
- Data engineers work in `jobs/etl/`, `jobs/marts_builder/`, `jobs/feature_builder/`, and `sql/`
- BI engineers work in `infra/superset/` and future dashboard assets
- Frontend engineers work in `apps/frontend/`

This split is deliberate so the hackathon team can move quickly without inventing project structure during implementation.

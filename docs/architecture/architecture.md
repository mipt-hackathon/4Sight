# Architecture Overview

This scaffold keeps backend, ML, BI, SQL, and batch responsibilities separate so the team can implement in parallel without inventing structure later.

## High-Level Architecture

```mermaid
flowchart LR
    raw["Mounted CSV Files\n(data.csv, events.csv)"] --> etl["ETL Jobs"]
    etl --> pg["PostgreSQL\nclean / mart / feature / serving"]
    pg --> backend["FastAPI Backend"]
    pg --> superset["Apache Superset"]
    pg --> ml["FastAPI ML API"]
    ml --> backend
    backend --> frontend["Next.js Frontend"]
    redis["Redis"] --> backend
    redis --> ml
```

## Docker Compose Services

```mermaid
flowchart TD
    postgres["postgres"]
    redis["redis"]
    backend["backend"]
    mlapi["ml-api"]
    frontend["frontend"]
    superset["superset"]
    pgadmin["pgadmin"]
    etl["etl"]
    marts["marts-builder"]
    features["feature-builder"]
    train["train"]
    scoring["batch-scoring"]

    postgres --> backend
    postgres --> mlapi
    postgres --> superset
    postgres --> pgadmin
    postgres --> etl
    postgres --> marts
    postgres --> features
    postgres --> train
    postgres --> scoring
    redis --> backend
    redis --> mlapi
    redis --> etl
    backend --> frontend
    mlapi --> backend
```

## Ownership Boundaries

- Backend owns product-facing API composition and future orchestration.
- ML API owns inference contracts and future artifact loading.
- Jobs own filesystem ingestion and batch refreshes.
- SQL folders own analytical dataset definitions.
- Superset consumes `mart` and `serving` through a read-only BI user.

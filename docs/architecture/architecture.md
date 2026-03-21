# Architecture Overview

This scaffold separates application APIs, ML interfaces, jobs, SQL, and BI assets so the team can build in parallel without blurring ownership.

## High-Level Architecture

```mermaid
flowchart LR
    raw["Mounted CSV Files\n(data.csv, events.csv)"] --> etl["ETL Jobs"]
    etl --> pg["PostgreSQL\nclean / mart / feature / serving"]
    pg --> backend["FastAPI Backend"]
    pg --> bi["Apache Superset"]
    pg --> ml["FastAPI ML API"]
    ml --> backend
    backend --> web["Next.js Frontend"]
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

- Backend owns product-facing API composition.
- ML API owns inference contracts and future model loading.
- Jobs own offline/batch workflows.
- SQL folders own analytical dataset definitions.
- Superset owns BI consumption, not source-of-truth business logic.

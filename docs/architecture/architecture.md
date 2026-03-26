
## High-Level data flow

```mermaid

flowchart LR
    data_csv["data.csv"] --> etl["jobs/ etl
    parsers / validators / extract / transform / load to db"]
    events_csv["events.csv"] --> etl
    etl --> clean["PostgreSQL очищенные таблички"]
    clean --> marts["jobs/marts_builder"]

    marts --> mart["PostgreSQL: витринные таблички"]
    mart --> features_job["jobs/feature_builder"] & backend["apps/backend"] & superset["Superset"]
    features_job --> feature["PostgreSQL: таблички с дополнительными показателями (под ML)"]
    feature --> train["jobs/train"] & batch["jobs/batch_scoring"] & mlapi["apps/ml_api"]
    train --> artifacts["artifacts/models/*"]
    artifacts --> batch & mlapi

    batch --> serving["PostgreSQL: итоговые таблички"]
    serving --> backend & superset
    backend --> frontend["apps/frontend"]
    mlapi <---> backend
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
    etl["etl"]
    marts["marts-builder"]
    features["feature-builder"]
    train["train"]
    scoring["batch-scoring"]

    postgres --> backend
    postgres --> mlapi
    postgres --> superset
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

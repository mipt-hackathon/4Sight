# Data Flow

The system treats the filesystem as the raw source and PostgreSQL as the home for curated analytical layers only.

## End-to-End Flow

```mermaid
flowchart LR
    raw["Mounted CSV Files"] --> parse["ETL Parse + Validate"]
    parse --> clean["clean schema"]
    clean --> mart["mart schema"]
    mart --> feature["feature schema"]
    feature --> train["Training Job"]
    feature --> score["ML API / Batch Scoring"]
    train --> artifacts["Model Artifacts"]
    artifacts --> score
    score --> serving["serving schema"]
    mart --> backend["Backend API"]
    serving --> backend
    mart --> superset["Superset"]
    serving --> superset
```

## PostgreSQL Layer Design

```mermaid
flowchart TD
    clean["clean\nvalidated base records"]
    mart["mart\nanalytics-friendly datasets"]
    feature["feature\nmodel-ready feature tables"]
    serving["serving\napplication and BI outputs"]

    clean --> mart
    mart --> feature
    feature --> serving
    mart --> serving
```

## Data Assumptions

- `data.csv` is a wide denormalized transactional dataset
- `events.csv` is a behavioral event log
- `events.csv` can contain missing `user_id`
- encoding cleanup may be required during ETL
- customer identity resolution will be implemented later
- raw CSV files stay on disk and are not loaded into PostgreSQL as raw replica tables

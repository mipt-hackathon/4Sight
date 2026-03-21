# Data Flow

The system is designed around mounted files as the raw source and PostgreSQL as the home for curated analytical layers only.

## End-to-End Flow

```mermaid
flowchart LR
    raw["Filesystem Mounted CSVs"] --> parse["ETL Parse + Validate"]
    parse --> clean["PostgreSQL clean schema"]
    clean --> mart["PostgreSQL mart schema"]
    mart --> feature["PostgreSQL feature schema"]
    feature --> train["Training Job"]
    feature --> ml["ML API / Batch Scoring"]
    train --> artifacts["Model Artifacts"]
    artifacts --> ml
    ml --> serving["PostgreSQL serving schema"]
    serving --> backend["Backend API"]
    serving --> superset["Superset Dashboards"]
    mart --> backend
    mart --> superset
```

## PostgreSQL Layer Design

```mermaid
flowchart TD
    clean["clean\nstandardized and validated base records"]
    mart["mart\nanalytics-friendly reusable marts"]
    feature["feature\nmodel-ready feature tables"]
    serving["serving\napplication and BI outputs"]

    clean --> mart
    mart --> feature
    feature --> serving
    mart --> serving
```

## Notes

- `data.csv` is expected to be wide and denormalized.
- `events.csv` can contain missing `user_id` values and encoding issues.
- Raw files stay on disk; ETL jobs are responsible for parsing and loading curated structures.

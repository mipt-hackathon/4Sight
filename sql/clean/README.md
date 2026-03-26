# Clean Schema SQL

Use this folder for SQL that defines and shapes ETL outputs into the `clean` schema.

- Inputs come from ETL-managed loads derived from mounted CSV files.
- Current source of truth for `clean.*` table DDL lives in these SQL files.
- The data.csv contract follows `notebooks/Анализ_data_csv.ipynb`:
  exact duplicate rows are dropped first, duplicate columns are removed, and only approved columns remain.
- SQL here should keep table contracts obvious and reviewable before mart/feature work starts.
- Do not treat filesystem CSVs as raw PostgreSQL replica tables.

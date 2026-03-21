# Clean Schema SQL

Use this folder for SQL that shapes ETL outputs into the `clean` schema.

- Inputs come from ETL-managed loads derived from mounted CSV files.
- SQL here should standardize types, keys, null handling, and deduplication.
- Do not treat filesystem CSVs as raw PostgreSQL replica tables.

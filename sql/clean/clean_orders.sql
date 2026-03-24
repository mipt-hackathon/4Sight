/*
Purpose:
  Define clean.orders after applying the notebook-backed data.csv cleaning contract.

Cleaning contract inherited from notebooks/Анализ_data_csv.ipynb:
  - drop exact duplicate rows from data.csv before splitting by entity
  - keep only order-level columns retained by the analyst
  - normalize ISO8601 timestamps during ETL loading
*/

CREATE TABLE clean.orders (
    etl_source_file TEXT NOT NULL DEFAULT 'data.csv',
    etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    status TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    num_of_item INTEGER NOT NULL
);

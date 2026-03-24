/*
Purpose:
  Define clean.users after applying the notebook-backed data.csv cleaning contract.

Cleaning contract inherited from notebooks/Анализ_data_csv.ipynb:
  - drop exact duplicate rows from data.csv before splitting by entity
  - keep user_id and drop duplicate id column
  - drop user_geom because its coordinates duplicate delivery_longitude / delivery_latitude
  - keep only analyst-approved user attributes
*/

CREATE TABLE clean.users (
    etl_source_file TEXT NOT NULL DEFAULT 'data.csv',
    etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id BIGINT PRIMARY KEY,
    gender TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    age INTEGER,
    state TEXT,
    street_address TEXT,
    postal_code TEXT,
    city TEXT,
    country TEXT,
    traffic_source TEXT,
    is_loyal BOOLEAN
);

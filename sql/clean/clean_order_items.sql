/*
Purpose:
  Define clean.order_items after applying the notebook-backed data.csv cleaning contract.

Cleaning contract inherited from notebooks/Анализ_data_csv.ipynb:
  - drop exact duplicate rows from data.csv before splitting by entity
  - remove duplicate columns:
      id, retail_price, product_retail_price, product_category, product_brand,
      product_department, product_sku, product_distribution_center_id,
      product_name_clean
  - remove geometry source columns:
      user_geom, distribution_center_geom
  - remove sold_at because the notebook drops it from the cleaned dataset
*/

CREATE TABLE clean.order_items (
    etl_source_file TEXT NOT NULL DEFAULT 'data.csv',
    etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    inventory_item_id BIGINT NOT NULL,
    sale_price NUMERIC NOT NULL,
    cost NUMERIC NOT NULL,
    category TEXT,
    brand TEXT,
    department TEXT,
    sku TEXT,
    distribution_center_id BIGINT NOT NULL,
    delivery_longitude DOUBLE PRECISION,
    delivery_latitude DOUBLE PRECISION,
    warehouse_name TEXT,
    warehouse_longitude DOUBLE PRECISION,
    warehouse_latitude DOUBLE PRECISION,
    product_name TEXT,
    customer_review TEXT
);

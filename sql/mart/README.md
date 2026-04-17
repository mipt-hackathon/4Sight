# Mart Schema SQL

Use this folder for analytical marts in the `mart` schema.

- Marts are consumer-friendly, reusable analytical datasets.
- Keep business logic here instead of in Alembic migrations.
- Typical outputs include customer 360, sales aggregates, logistics, cohort, and RFM marts.
- The current runnable mart layer includes:
  - `mart_sales_daily.sql`
  - `mart_behavior_metrics.sql`
  - `mart_customer_360.sql`
  - `mart_abc_xyz.sql`
  - `mart_rfm.sql`
  - `mart_logistics_metrics.sql`
  - `mart_cohorts.sql`
  - `mart_product_xyz.sql`
  - `mart_region_abc.sql`
  - `mart_customer_abc_monthly.sql`
  - `mart_customer_category_migration.sql`
  - `mart_category_abc.sql`
  - `mart_brand_abc.sql`

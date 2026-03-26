# Mart Schema SQL

Use this folder for analytical marts in the `mart` schema.

- Marts are consumer-friendly, reusable analytical datasets.
- Keep business logic here instead of in Alembic migrations.
- Typical outputs include customer 360, sales aggregates, logistics, cohort, and RFM marts.
- The first runnable baseline currently includes:
  - `mart_sales_daily.sql`
  - `mart_behavior_metrics.sql`
  - `mart_customer_360.sql`
  - `mart_rfm.sql`

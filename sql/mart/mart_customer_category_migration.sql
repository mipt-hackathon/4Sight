/*
Purpose:
  Build notebook-backed customer product-category migration matrix.

Notebook nuance:
  - The source notebook calculates migration on first and last product category
    per user, not on first and last ABC category.
  - This SQL reproduces that logic literally.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.customer_category_migration

Grain:
  - one row per first_category and last_category combination
*/

DROP TABLE IF EXISTS mart.customer_category_migration;

CREATE TABLE mart.customer_category_migration AS
WITH ordered_categories AS (
    SELECT
        oi.user_id,
        date_trunc('month', o.created_at)::date AS year_month,
        oi.category,
        ROW_NUMBER() OVER (
            PARTITION BY oi.user_id
            ORDER BY o.created_at, oi.order_item_id
        ) AS first_rn,
        ROW_NUMBER() OVER (
            PARTITION BY oi.user_id
            ORDER BY o.created_at DESC, oi.order_item_id DESC
        ) AS last_rn
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
),
customer_first_last AS (
    SELECT
        user_id,
        MAX(year_month) FILTER (WHERE first_rn = 1) AS first_month,
        MAX(year_month) FILTER (WHERE last_rn = 1) AS last_month,
        MAX(category) FILTER (WHERE first_rn = 1) AS first_category,
        MAX(category) FILTER (WHERE last_rn = 1) AS last_category
    FROM ordered_categories
    GROUP BY user_id
),
migration_counts AS (
    SELECT
        COALESCE(first_category, 'Unknown') AS first_category,
        COALESCE(last_category, 'Unknown') AS last_category,
        COUNT(*) AS customers_count
    FROM customer_first_last
    GROUP BY
        COALESCE(first_category, 'Unknown'),
        COALESCE(last_category, 'Unknown')
),
category_totals AS (
    SELECT
        first_category,
        SUM(customers_count) AS first_category_total,
        SUM(
            CASE
                WHEN first_category = last_category THEN customers_count
                ELSE 0
            END
        ) AS stable_customers
    FROM migration_counts
    GROUP BY first_category
)
SELECT
    migration_counts.first_category,
    migration_counts.last_category,
    migration_counts.customers_count,
    category_totals.first_category_total,
    ROUND(
        100.0 * migration_counts.customers_count
        / NULLIF(category_totals.first_category_total, 0),
        2
    ) AS migration_percent,
    ROUND(
        100.0 * category_totals.stable_customers
        / NULLIF(category_totals.first_category_total, 0),
        2
    ) AS category_stability_percent
FROM migration_counts
JOIN category_totals
    ON category_totals.first_category = migration_counts.first_category
ORDER BY migration_counts.first_category, migration_counts.last_category;

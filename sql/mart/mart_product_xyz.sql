/*
Purpose:
  Build notebook-backed product stability mart for demand volatility analysis.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.product_xyz

Grain:
  - one row per product_id with at least 3 active months
*/

DROP TABLE IF EXISTS mart.product_xyz;

CREATE TABLE mart.product_xyz AS
WITH product_source AS (
    SELECT
        oi.order_item_id,
        oi.product_id,
        oi.product_name,
        oi.category,
        oi.brand,
        oi.department,
        oi.user_id,
        oi.order_id,
        COALESCE(oi.sale_price, 0)::NUMERIC(14, 2) AS sale_price,
        COALESCE(oi.cost, 0)::NUMERIC(14, 2) AS cost,
        date_trunc('month', o.created_at)::date AS year_month,
        o.created_at,
        o.returned_at
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
),
product_monthly AS (
    SELECT
        product_id,
        year_month,
        SUM(sale_price)::NUMERIC(14, 2) AS sale_price
    FROM product_source
    GROUP BY product_id, year_month
),
active_products AS (
    SELECT
        product_id,
        COUNT(*) AS month_count
    FROM product_monthly
    GROUP BY product_id
    HAVING COUNT(*) >= 3
),
product_stats AS (
    SELECT
        product_monthly.product_id,
        active_products.month_count,
        ROUND(AVG(product_monthly.sale_price), 2) AS avg_sales,
        ROUND(COALESCE(STDDEV_SAMP(product_monthly.sale_price), 0)::NUMERIC, 2) AS std_sales,
        ROUND(
            COALESCE(
                COALESCE(STDDEV_SAMP(product_monthly.sale_price), 0)
                / NULLIF(AVG(product_monthly.sale_price), 0),
                0
            )::NUMERIC,
            4
        ) AS cv_sales,
        CASE
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(product_monthly.sale_price), 0)
                / NULLIF(AVG(product_monthly.sale_price), 0),
                0
            ) < 0.3 THEN 'X (стабильные)'
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(product_monthly.sale_price), 0)
                / NULLIF(AVG(product_monthly.sale_price), 0),
                0
            ) < 0.7 THEN 'Y (средние)'
            ELSE 'Z (нестабильные)'
        END AS xyz_category
    FROM product_monthly
    JOIN active_products
        ON active_products.product_id = product_monthly.product_id
    GROUP BY product_monthly.product_id, active_products.month_count
),
product_totals AS (
    SELECT
        product_source.product_id,
        MIN(product_source.product_name) AS product_name,
        MIN(product_source.category) AS category,
        MIN(product_source.brand) AS brand,
        MIN(product_source.department) AS department,
        MIN(product_source.created_at) AS first_sold_at,
        MAX(product_source.created_at) AS last_sold_at,
        COUNT(product_source.order_item_id) AS units_sold,
        COUNT(DISTINCT product_source.order_id) AS orders_count,
        COUNT(DISTINCT product_source.user_id) AS customers_count,
        COALESCE(SUM(product_source.sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        COALESCE(SUM(product_source.sale_price - product_source.cost), 0)::NUMERIC(14, 2) AS total_profit,
        COUNT(*) FILTER (WHERE product_source.returned_at IS NOT NULL) AS return_count,
        CASE
            WHEN COUNT(product_source.order_item_id) = 0 THEN 0::NUMERIC(10, 4)
            ELSE ROUND(
                (COUNT(*) FILTER (WHERE product_source.returned_at IS NOT NULL))::NUMERIC
                / COUNT(product_source.order_item_id),
                4
            )
        END AS return_rate
    FROM product_source
    GROUP BY product_source.product_id
)
SELECT
    product_totals.product_id,
    product_totals.product_name,
    product_totals.category,
    product_totals.brand,
    product_totals.department,
    product_totals.first_sold_at,
    product_totals.last_sold_at,
    product_totals.units_sold,
    product_totals.orders_count,
    product_totals.customers_count,
    product_totals.total_revenue,
    product_totals.total_profit,
    product_totals.return_count,
    product_totals.return_rate,
    product_stats.month_count,
    product_stats.avg_sales,
    product_stats.std_sales,
    product_stats.cv_sales,
    product_stats.xyz_category
FROM product_totals
JOIN product_stats
    ON product_stats.product_id = product_totals.product_id
ORDER BY product_stats.cv_sales DESC, product_totals.product_id;

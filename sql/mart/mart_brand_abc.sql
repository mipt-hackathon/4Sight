/*
Purpose:
  Build ABC analysis by brand for assortment and merchandising review.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.brand_abc

Grain:
  - one row per brand
*/

DROP TABLE IF EXISTS mart.brand_abc;

CREATE TABLE mart.brand_abc AS
WITH brand_base AS (
    SELECT
        COALESCE(oi.brand, 'Unknown') AS brand,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        COALESCE(SUM(oi.sale_price - oi.cost), 0)::NUMERIC(14, 2) AS total_profit,
        COUNT(*) AS units_sold,
        COUNT(DISTINCT oi.order_id) AS orders_count,
        COUNT(DISTINCT oi.user_id) AS customers_count,
        COUNT(*) FILTER (WHERE o.returned_at IS NOT NULL) AS return_count,
        CASE
            WHEN COUNT(*) = 0 THEN 0::NUMERIC(10, 4)
            ELSE ROUND(
                (COUNT(*) FILTER (WHERE o.returned_at IS NOT NULL))::NUMERIC
                / COUNT(*),
                4
            )
        END AS return_rate
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
    GROUP BY COALESCE(oi.brand, 'Unknown')
),
brand_ranked AS (
    SELECT
        brand,
        total_revenue,
        total_profit,
        units_sold,
        orders_count,
        customers_count,
        return_count,
        return_rate,
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC, brand
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS revenue_cumsum,
        100.0 * SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC, brand
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / NULLIF(SUM(total_revenue) OVER (), 0) AS revenue_cumpercent
    FROM brand_base
)
SELECT
    brand,
    total_revenue,
    total_profit,
    units_sold,
    orders_count,
    customers_count,
    return_count,
    return_rate,
    revenue_cumsum,
    ROUND(revenue_cumpercent::NUMERIC, 2) AS revenue_cumpercent,
    CASE
        WHEN revenue_cumpercent <= 20 THEN 'A'
        WHEN revenue_cumpercent <= 50 THEN 'B'
        ELSE 'C'
    END AS abc_category
FROM brand_ranked
ORDER BY total_revenue DESC, brand;

/*
Purpose:
  Build notebook-backed regional ABC analysis for sales geography.

Expected inputs:
  - clean.orders
  - clean.order_items
  - clean.users

Expected outputs:
  - mart.region_abc

Grain:
  - one row per state
*/

DROP TABLE IF EXISTS mart.region_abc;

CREATE TABLE mart.region_abc AS
WITH region_base AS (
    SELECT
        COALESCE(u.state, 'Unknown') AS state,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        COALESCE(SUM(oi.sale_price - oi.cost), 0)::NUMERIC(14, 2) AS total_profit,
        COUNT(DISTINCT oi.user_id) AS customers_count,
        COUNT(oi.order_id) AS order_count
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
    JOIN clean.users AS u
        ON u.user_id = o.user_id
    GROUP BY COALESCE(u.state, 'Unknown')
),
region_ranked AS (
    SELECT
        state,
        total_revenue,
        total_profit,
        customers_count,
        order_count,
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC, state
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS revenue_cumsum,
        100.0 * SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC, state
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / NULLIF(SUM(total_revenue) OVER (), 0) AS revenue_cumpercent
    FROM region_base
)
SELECT
    state,
    total_revenue,
    total_profit,
    customers_count,
    order_count,
    revenue_cumsum,
    ROUND(revenue_cumpercent::NUMERIC, 2) AS revenue_cumpercent,
    CASE
        WHEN revenue_cumpercent <= 80 THEN 'A (ключевые регионы)'
        WHEN revenue_cumpercent <= 95 THEN 'B (развивающиеся)'
        ELSE 'C (периферия)'
    END AS region_category
FROM region_ranked
ORDER BY total_revenue DESC, state;

/*
Purpose:
  Build a daily sales mart for BI, monitoring, and forecasting use cases.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.sales_daily

Grain:
  - one row per order creation date
*/

DROP TABLE IF EXISTS mart.sales_daily;

CREATE TABLE mart.sales_daily AS
WITH daily_sales AS (
    SELECT
        o.created_at::date AS sales_date,
        COUNT(DISTINCT o.order_id) AS orders_count,
        COUNT(DISTINCT o.user_id) AS customers_count,
        COUNT(oi.order_item_id) AS order_items_count,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS gross_revenue,
        COALESCE(AVG(oi.sale_price), 0)::NUMERIC(14, 2) AS avg_item_price,
        COUNT(DISTINCT CASE WHEN o.status = 'Complete' THEN o.order_id END) AS completed_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Shipped' THEN o.order_id END) AS shipped_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Cancelled' THEN o.order_id END) AS cancelled_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) AS returned_orders_count
    FROM clean.orders AS o
    JOIN clean.order_items AS oi
        ON oi.order_id = o.order_id
    GROUP BY 1
)
SELECT
    sales_date,
    orders_count,
    customers_count,
    order_items_count,
    gross_revenue,
    avg_item_price,
    CASE
        WHEN orders_count = 0 THEN 0::NUMERIC(14, 2)
        ELSE ROUND(gross_revenue / orders_count, 2)
    END AS avg_order_value,
    completed_orders_count,
    shipped_orders_count,
    cancelled_orders_count,
    returned_orders_count
FROM daily_sales
ORDER BY sales_date;

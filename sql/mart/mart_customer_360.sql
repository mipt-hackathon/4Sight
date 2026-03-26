/*
Purpose:
  Build a reusable customer 360 mart joining sales, loyalty, behavior, and service context.

Expected inputs:
  - clean.users
  - clean.orders
  - clean.order_items
  - mart.behavior_metrics

Expected outputs:
  - mart.customer_360

Grain:
  - one row per user_id
*/

DROP TABLE IF EXISTS mart.customer_360;

CREATE TABLE mart.customer_360 AS
WITH order_metrics AS (
    SELECT
        o.user_id,
        MIN(o.created_at) AS first_order_at,
        MAX(o.created_at) AS last_order_at,
        COUNT(DISTINCT o.order_id) AS orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Complete' THEN o.order_id END) AS completed_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Shipped' THEN o.order_id END) AS shipped_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Cancelled' THEN o.order_id END) AS cancelled_orders_count,
        COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) AS returned_orders_count,
        COUNT(oi.order_item_id) AS order_items_count,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(o.created_at)))::INTEGER AS days_since_last_order
    FROM clean.orders AS o
    JOIN clean.order_items AS oi
        ON oi.order_id = o.order_id
    GROUP BY 1
)
SELECT
    u.user_id,
    u.gender,
    u.first_name,
    u.last_name,
    u.email,
    u.age,
    u.state,
    u.city,
    u.country,
    u.traffic_source,
    u.is_loyal,
    om.first_order_at,
    om.last_order_at,
    COALESCE(om.orders_count, 0) AS orders_count,
    COALESCE(om.completed_orders_count, 0) AS completed_orders_count,
    COALESCE(om.shipped_orders_count, 0) AS shipped_orders_count,
    COALESCE(om.cancelled_orders_count, 0) AS cancelled_orders_count,
    COALESCE(om.returned_orders_count, 0) AS returned_orders_count,
    COALESCE(om.order_items_count, 0) AS order_items_count,
    COALESCE(om.total_revenue, 0)::NUMERIC(14, 2) AS total_revenue,
    CASE
        WHEN COALESCE(om.orders_count, 0) = 0 THEN 0::NUMERIC(14, 2)
        ELSE ROUND(om.total_revenue / om.orders_count, 2)
    END AS avg_order_value,
    om.days_since_last_order,
    bm.first_event_at,
    bm.last_event_at,
    COALESCE(bm.event_count, 0) AS event_count,
    COALESCE(bm.session_count, 0) AS session_count,
    COALESCE(bm.home_events_count, 0) AS home_events_count,
    COALESCE(bm.department_events_count, 0) AS department_events_count,
    COALESCE(bm.product_events_count, 0) AS product_events_count,
    COALESCE(bm.cart_events_count, 0) AS cart_events_count,
    COALESCE(bm.purchase_events_count, 0) AS purchase_events_count,
    COALESCE(bm.cancel_events_count, 0) AS cancel_events_count,
    bm.days_since_last_event
FROM clean.users AS u
LEFT JOIN order_metrics AS om
    ON om.user_id = u.user_id
LEFT JOIN mart.behavior_metrics AS bm
    ON bm.user_id = u.user_id
ORDER BY u.user_id;

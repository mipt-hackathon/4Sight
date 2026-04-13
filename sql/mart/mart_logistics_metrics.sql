/*
Purpose:
  Build notebook-backed logistics, delivery, and returns metrics.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.logistics_metrics

Grain:
  - one row per user_id
*/

DROP TABLE IF EXISTS mart.logistics_metrics;

CREATE TABLE mart.logistics_metrics AS
WITH delivery_returns AS (
    SELECT
        oi.order_item_id,
        oi.user_id,
        oi.order_id,
        date_trunc('month', o.created_at)::date AS year_month,
        o.created_at,
        o.shipped_at,
        o.delivered_at,
        o.returned_at,
        COALESCE(oi.sale_price, 0)::NUMERIC(14, 2) AS sale_price,
        CASE
            WHEN o.delivered_at IS NOT NULL AND o.shipped_at IS NOT NULL THEN
                (o.delivered_at::date - o.shipped_at::date)
            ELSE NULL
        END AS delivery_days,
        CASE
            WHEN o.returned_at IS NOT NULL AND o.delivered_at IS NOT NULL THEN
                (o.returned_at::date - o.delivered_at::date)
            ELSE NULL
        END AS return_days_after_delivery,
        CASE
            WHEN o.returned_at IS NOT NULL THEN 1
            ELSE 0
        END AS is_returned
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
),
snapshot AS (
    SELECT MAX(created_at)::date AS current_date
    FROM delivery_returns
),
monthly_returns AS (
    SELECT
        user_id,
        year_month,
        SUM(is_returned) AS return_count,
        COUNT(order_id) AS order_count
    FROM delivery_returns
    GROUP BY user_id, year_month
),
active_users AS (
    SELECT
        user_id,
        COUNT(*) AS month_count
    FROM monthly_returns
    GROUP BY user_id
    HAVING COUNT(*) >= 3
),
returns_xyz AS (
    SELECT
        monthly_returns.user_id,
        active_users.month_count,
        ROUND(AVG(monthly_returns.return_count::NUMERIC), 4) AS avg_returns,
        ROUND(COALESCE(STDDEV_SAMP(monthly_returns.return_count::NUMERIC), 0)::NUMERIC, 4) AS std_returns,
        ROUND(
            COALESCE(
                COALESCE(STDDEV_SAMP(monthly_returns.return_count::NUMERIC), 0)
                / NULLIF(AVG(monthly_returns.return_count::NUMERIC), 0),
                0
            )::NUMERIC,
            4
        ) AS cv_returns,
        CASE
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(monthly_returns.return_count::NUMERIC), 0)
                / NULLIF(AVG(monthly_returns.return_count::NUMERIC), 0),
                0
            ) < 0.3 THEN 'X (стабильные возвраты)'
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(monthly_returns.return_count::NUMERIC), 0)
                / NULLIF(AVG(monthly_returns.return_count::NUMERIC), 0),
                0
            ) < 0.7 THEN 'Y (средние)'
            ELSE 'Z (нестабильные возвраты)'
        END AS returns_xyz_category
    FROM monthly_returns
    JOIN active_users
        ON active_users.user_id = monthly_returns.user_id
    GROUP BY monthly_returns.user_id, active_users.month_count
),
client_delivery_returns AS (
    SELECT
        user_id,
        ROUND(AVG(delivery_days::NUMERIC), 2) AS avg_delivery_days,
        ROUND(AVG(is_returned::NUMERIC), 4) AS return_rate,
        COUNT(order_id) AS total_orders,
        SUM(is_returned) AS return_count,
        ROUND(AVG(return_days_after_delivery::NUMERIC), 2) AS avg_return_days_after_delivery,
        COALESCE(SUM(sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        MAX(created_at) AS last_order_at
    FROM delivery_returns
    GROUP BY user_id
),
delivery_bounds AS (
    SELECT NULLIF(MAX(avg_delivery_days), 0) AS max_avg_delivery_days
    FROM client_delivery_returns
)
SELECT
    client_delivery_returns.user_id,
    client_delivery_returns.avg_delivery_days,
    client_delivery_returns.avg_return_days_after_delivery,
    client_delivery_returns.total_orders,
    client_delivery_returns.return_count,
    client_delivery_returns.return_rate,
    client_delivery_returns.total_revenue,
    client_delivery_returns.last_order_at,
    (snapshot.current_date - client_delivery_returns.last_order_at::date) AS recency_days,
    CASE
        WHEN (snapshot.current_date - client_delivery_returns.last_order_at::date) > 60 THEN 1
        ELSE 0
    END AS churn,
    COALESCE(returns_xyz.month_count, 0) AS month_count,
    CASE
        WHEN client_delivery_returns.avg_delivery_days <= 3 THEN 'Быстрая доставка'
        WHEN client_delivery_returns.avg_delivery_days <= 7 THEN 'Нормальная доставка'
        ELSE 'Медленная доставка'
    END AS delivery_category,
    CASE
        WHEN client_delivery_returns.return_rate = 0 THEN 'Нет возвратов'
        WHEN client_delivery_returns.return_rate <= 0.2 THEN 'Редкие возвраты'
        ELSE 'Частые возвраты'
    END AS returns_category,
    returns_xyz.returns_xyz_category,
    ROUND(
        (
            client_delivery_returns.return_rate * 0.6
            + COALESCE(
                client_delivery_returns.avg_delivery_days / delivery_bounds.max_avg_delivery_days,
                0
            ) * 0.4
        )::NUMERIC,
        4
    ) AS problem_score,
    CASE
        WHEN client_delivery_returns.return_rate > 0.3
            AND client_delivery_returns.avg_delivery_days > 7 THEN
            '🔴 КРИТИЧНО: Проверить качество товаров и логистику'
        WHEN client_delivery_returns.return_rate > 0.2 THEN
            '🟡 ВНИМАНИЕ: Высокая доля возвратов, проверить ассортимент'
        WHEN client_delivery_returns.avg_delivery_days > 7 THEN
            '🟡 ВНИМАНИЕ: Медленная доставка, оптимизировать логистику'
        ELSE '🟢 Нормально'
    END AS recommendation
FROM client_delivery_returns
CROSS JOIN snapshot
CROSS JOIN delivery_bounds
LEFT JOIN returns_xyz
    ON returns_xyz.user_id = client_delivery_returns.user_id
ORDER BY problem_score DESC, client_delivery_returns.user_id;

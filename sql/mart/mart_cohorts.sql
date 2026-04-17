/*
Purpose:
  Build cohort analysis outputs for retention and customer lifecycle monitoring.

Expected inputs:
  - clean.users
  - clean.order_items
  - clean.events

Expected outputs:
  - mart.cohorts

Grain:
  - one row per cohort_month and cohort_period_number
*/

DROP TABLE IF EXISTS mart.cohorts;

CREATE TABLE mart.cohorts AS
WITH order_revenue AS (
    SELECT
        o.user_id,
        o.order_id,
        date_trunc('month', o.created_at)::date AS activity_month,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS order_revenue
    FROM clean.orders AS o
    JOIN clean.order_items AS oi
        ON oi.order_id = o.order_id
    GROUP BY
        o.user_id,
        o.order_id,
        date_trunc('month', o.created_at)::date
),
order_with_cohort AS (
    SELECT
        user_id,
        order_id,
        activity_month,
        order_revenue,
        MIN(activity_month) OVER (PARTITION BY user_id) AS cohort_month
    FROM order_revenue
),
cohort_activity AS (
    SELECT
        cohort_month,
        activity_month,
        (
            (EXTRACT(YEAR FROM activity_month) * 12 + EXTRACT(MONTH FROM activity_month))
            - (EXTRACT(YEAR FROM cohort_month) * 12 + EXTRACT(MONTH FROM cohort_month))
        )::INT AS cohort_period_number,
        COUNT(DISTINCT user_id) AS active_customers,
        COUNT(DISTINCT order_id) AS orders_count,
        COALESCE(SUM(order_revenue), 0)::NUMERIC(14, 2) AS revenue
    FROM order_with_cohort
    GROUP BY
        cohort_month,
        activity_month,
        (
            (EXTRACT(YEAR FROM activity_month) * 12 + EXTRACT(MONTH FROM activity_month))
            - (EXTRACT(YEAR FROM cohort_month) * 12 + EXTRACT(MONTH FROM cohort_month))
        )
),
cohort_sizes AS (
    SELECT
        cohort_month,
        active_customers AS cohort_size
    FROM cohort_activity
    WHERE cohort_period_number = 0
)
SELECT
    cohort_activity.cohort_month,
    cohort_activity.activity_month,
    cohort_activity.cohort_period_number,
    cohort_sizes.cohort_size,
    cohort_activity.active_customers,
    cohort_activity.orders_count,
    cohort_activity.revenue,
    CASE
        WHEN cohort_sizes.cohort_size = 0 THEN 0::NUMERIC(10, 4)
        ELSE ROUND(
            cohort_activity.active_customers::NUMERIC
            / cohort_sizes.cohort_size,
            4
        )
    END AS retention_rate,
    CASE
        WHEN cohort_activity.active_customers = 0 THEN 0::NUMERIC(14, 2)
        ELSE ROUND(
            cohort_activity.revenue
            / cohort_activity.active_customers,
            2
        )
    END AS avg_revenue_per_active_customer
FROM cohort_activity
JOIN cohort_sizes
    ON cohort_sizes.cohort_month = cohort_activity.cohort_month
ORDER BY cohort_activity.cohort_month, cohort_activity.cohort_period_number;

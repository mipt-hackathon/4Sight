/*
Purpose:
  Build notebook-backed sample monthly time series for corrected ABC/XYZ categories.

Expected inputs:
  - clean.orders
  - clean.order_items
  - mart.abc_xyz

Expected outputs:
  - mart.abc_xyz_time_series_samples

Grain:
  - one row per time_period
*/

DROP TABLE IF EXISTS mart.abc_xyz_time_series_samples;

CREATE TABLE mart.abc_xyz_time_series_samples AS
WITH time_series AS (
    SELECT
        oi.user_id,
        date_trunc('month', o.created_at)::date AS time_period,
        SUM(COALESCE(oi.sale_price, 0))::NUMERIC(14, 2) AS period_value
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
    GROUP BY oi.user_id, date_trunc('month', o.created_at)::date
),
sample_users AS (
    SELECT
        xyz_category,
        user_id,
        cv_percent,
        ROW_NUMBER() OVER (
            PARTITION BY xyz_category
            ORDER BY total_revenue DESC, user_id
        ) AS row_number
    FROM mart.abc_xyz
    WHERE xyz_category IN ('X', 'Y', 'Z')
),
selected_samples AS (
    SELECT
        xyz_category,
        user_id,
        cv_percent
    FROM sample_users
    WHERE row_number = 1
),
sampled_series AS (
    SELECT
        selected_samples.xyz_category,
        selected_samples.user_id,
        selected_samples.cv_percent,
        time_series.time_period,
        time_series.period_value
    FROM selected_samples
    JOIN time_series
        ON time_series.user_id = selected_samples.user_id
)
SELECT
    time_period,
    MAX(CASE WHEN xyz_category = 'X' THEN user_id END) AS x_sample_user_id,
    MAX(CASE WHEN xyz_category = 'X' THEN ROUND(cv_percent::NUMERIC, 2) END) AS x_cv_percent,
    MAX(CASE WHEN xyz_category = 'X' THEN period_value END) AS x_period_value,
    MAX(CASE WHEN xyz_category = 'Y' THEN user_id END) AS y_sample_user_id,
    MAX(CASE WHEN xyz_category = 'Y' THEN ROUND(cv_percent::NUMERIC, 2) END) AS y_cv_percent,
    MAX(CASE WHEN xyz_category = 'Y' THEN period_value END) AS y_period_value,
    MAX(CASE WHEN xyz_category = 'Z' THEN user_id END) AS z_sample_user_id,
    MAX(CASE WHEN xyz_category = 'Z' THEN ROUND(cv_percent::NUMERIC, 2) END) AS z_cv_percent,
    MAX(CASE WHEN xyz_category = 'Z' THEN period_value END) AS z_period_value
FROM sampled_series
GROUP BY time_period
ORDER BY time_period;

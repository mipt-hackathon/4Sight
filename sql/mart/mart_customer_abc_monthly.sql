/*
Purpose:
  Build notebook-backed monthly ABC distribution of customers.

Notebook nuance:
  - The source notebook classifies each customer's monthly revenue against
    fixed half / eighty-percent thresholds of the whole month's revenue,
    not against cumulative ABC ranks.
  - This SQL reproduces that logic literally.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.customer_abc_monthly

Grain:
  - one row per year_month
*/

DROP TABLE IF EXISTS mart.customer_abc_monthly;

CREATE TABLE mart.customer_abc_monthly AS
WITH monthly_customer_data AS (
    SELECT
        oi.user_id,
        date_trunc('month', o.created_at)::date AS year_month,
        COALESCE(SUM(oi.sale_price), 0)::NUMERIC(14, 2) AS sale_price,
        COUNT(DISTINCT oi.order_id) AS order_count,
        COALESCE(SUM(oi.sale_price - oi.cost), 0)::NUMERIC(14, 2) AS profit
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
    GROUP BY
        oi.user_id,
        date_trunc('month', o.created_at)::date
),
month_totals AS (
    SELECT
        year_month,
        SUM(sale_price)::NUMERIC(14, 2) AS month_total_revenue
    FROM monthly_customer_data
    GROUP BY year_month
),
monthly_categories AS (
    SELECT
        monthly_customer_data.user_id,
        monthly_customer_data.year_month,
        monthly_customer_data.sale_price,
        monthly_customer_data.order_count,
        monthly_customer_data.profit,
        CASE
            WHEN monthly_customer_data.sale_price <= month_totals.month_total_revenue * 0.5 THEN 'C'
            WHEN monthly_customer_data.sale_price <= month_totals.month_total_revenue * 0.8 THEN 'B'
            ELSE 'A'
        END AS monthly_category
    FROM monthly_customer_data
    JOIN month_totals
        ON month_totals.year_month = monthly_customer_data.year_month
),
monthly_distribution AS (
    SELECT
        year_month,
        COUNT(*) FILTER (WHERE monthly_category = 'A') AS a_customers,
        COUNT(*) FILTER (WHERE monthly_category = 'B') AS b_customers,
        COUNT(*) FILTER (WHERE monthly_category = 'C') AS c_customers,
        COUNT(*) AS total_customers
    FROM monthly_categories
    GROUP BY year_month
)
SELECT
    year_month,
    a_customers,
    b_customers,
    c_customers,
    total_customers,
    ROUND(100.0 * a_customers / NULLIF(total_customers, 0), 2) AS a_percent,
    ROUND(100.0 * b_customers / NULLIF(total_customers, 0), 2) AS b_percent,
    ROUND(100.0 * c_customers / NULLIF(total_customers, 0), 2) AS c_percent
FROM monthly_distribution
ORDER BY year_month;

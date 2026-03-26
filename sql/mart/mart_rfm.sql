/*
Purpose:
  Build RFM measures for segmentation and churn analysis.

Expected inputs:
  - mart.customer_360

Expected outputs:
  - mart.rfm

Grain:
  - one row per user_id
*/

DROP TABLE IF EXISTS mart.rfm;

CREATE TABLE mart.rfm AS
WITH rfm_base AS (
    SELECT
        user_id,
        COALESCE(days_since_last_order, 999999) AS recency_days,
        COALESCE(orders_count, 0) AS frequency_orders,
        COALESCE(total_revenue, 0)::NUMERIC(14, 2) AS monetary_value
    FROM mart.customer_360
),
rfm_scored AS (
    SELECT
        user_id,
        recency_days,
        frequency_orders,
        monetary_value,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC, user_id) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency_orders ASC, user_id) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary_value ASC, user_id) AS monetary_score
    FROM rfm_base
)
SELECT
    user_id,
    recency_days,
    frequency_orders,
    monetary_value,
    recency_score,
    frequency_score,
    monetary_score,
    CONCAT(recency_score, frequency_score, monetary_score) AS rfm_score,
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'champions'
        WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'loyal'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'at_risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'hibernating'
        ELSE 'potential_loyalist'
    END AS rfm_segment
FROM rfm_scored
ORDER BY user_id;

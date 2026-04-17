/*
Purpose:
  Build notebook-backed RFM measures for segmentation and churn analysis.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.rfm

Grain:
  - one row per user_id
*/

DROP TABLE IF EXISTS mart.rfm;

CREATE TABLE mart.rfm AS
WITH analysis_source AS (
    SELECT
        oi.user_id,
        oi.order_id,
        COALESCE(oi.sale_price, 0)::NUMERIC(14, 2) AS sale_price,
        o.created_at
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
),
snapshot AS (
    SELECT MAX(created_at) AS current_date
    FROM analysis_source
),
rfm_base AS (
    SELECT
        analysis_source.user_id,
        (snapshot.current_date::date - MAX(analysis_source.created_at)::date) AS recency,
        COUNT(DISTINCT analysis_source.order_id) AS frequency,
        COALESCE(SUM(analysis_source.sale_price), 0)::NUMERIC(14, 2) AS monetary
    FROM analysis_source
    CROSS JOIN snapshot
    GROUP BY analysis_source.user_id, snapshot.current_date
),
rfm_scored AS (
    SELECT
        user_id,
        recency,
        frequency,
        monetary,
        CASE
            WHEN frequency = 0 THEN 0::NUMERIC(14, 2)
            ELSE ROUND(monetary / frequency, 2)
        END AS avg_order_value,
        5 - NTILE(4) OVER (ORDER BY recency ASC, user_id) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC, user_id) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC, user_id) AS m_score
    FROM rfm_base
),
rfm_segmented AS (
    SELECT
        user_id,
        recency,
        frequency,
        monetary,
        avg_order_value,
        r_score,
        f_score,
        m_score,
        CONCAT(r_score, f_score, m_score) AS rfm_score,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '👑 Champions (лучшие клиенты)'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN '⭐ Loyal (лояльные)'
            WHEN r_score >= 4 AND f_score <= 2 THEN '🚀 Potential (перспективные)'
            WHEN r_score <= 2 AND f_score >= 3 THEN '⚠️ At Risk (под риском)'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN '🔔 Need Attention (требуют внимания)'
            WHEN r_score = 2 AND f_score = 2 THEN '😴 About to Sleep (засыпающие)'
            WHEN r_score = 1 THEN '💀 Lost (потерянные)'
            WHEN f_score = 1 AND r_score >= 3 THEN '🆕 New (новые)'
            ELSE '📊 Regular (обычные)'
        END AS segment,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'champions'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'loyal'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'at_risk'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'hibernating'
            ELSE 'potential_loyalist'
        END AS rfm_segment
    FROM rfm_scored
)
SELECT
    user_id,
    recency,
    frequency,
    monetary,
    avg_order_value,
    r_score,
    f_score,
    m_score,
    rfm_score,
    rfm_total,
    segment,
    recency AS recency_days,
    frequency AS frequency_orders,
    monetary AS monetary_value,
    r_score AS recency_score,
    f_score AS frequency_score,
    m_score AS monetary_score,
    rfm_segment
FROM rfm_segmented
ORDER BY user_id;

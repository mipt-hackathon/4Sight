/*
Purpose:
  Build notebook-backed churn summary by RFM segment.

Expected inputs:
  - mart.rfm
  - mart.abc_xyz

Expected outputs:
  - mart.rfm_churn_by_segment

Grain:
  - one row per segment
*/

DROP TABLE IF EXISTS mart.rfm_churn_by_segment;

CREATE TABLE mart.rfm_churn_by_segment AS
SELECT
    rfm.segment,
    COUNT(*) AS customers_count,
    ROUND(AVG(COALESCE(abc_xyz.churn, 0)::NUMERIC), 4) AS churn_rate,
    ROUND(AVG(rfm.recency::NUMERIC), 2) AS avg_recency,
    ROUND(AVG(rfm.frequency::NUMERIC), 2) AS avg_frequency,
    ROUND(AVG(rfm.monetary::NUMERIC), 2) AS avg_monetary,
    ROUND(AVG(rfm.avg_order_value::NUMERIC), 2) AS avg_order_value,
    ROUND(AVG(rfm.rfm_total::NUMERIC), 2) AS avg_rfm_total
FROM mart.rfm AS rfm
LEFT JOIN mart.abc_xyz AS abc_xyz
    ON abc_xyz.user_id = rfm.user_id
GROUP BY rfm.segment
ORDER BY churn_rate DESC, customers_count DESC, rfm.segment;

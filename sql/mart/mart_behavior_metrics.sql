/*
Purpose:
  Build behavioral usage metrics from cleaned event data.

Expected inputs:
  - clean.events

Expected outputs:
  - mart.behavior_metrics

Grain:
  - one row per known user_id
*/

DROP TABLE IF EXISTS mart.behavior_metrics;

CREATE TABLE mart.behavior_metrics AS
SELECT
    user_id,
    MIN(created_at) AS first_event_at,
    MAX(created_at) AS last_event_at,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_id) AS session_count,
    COUNT(*) FILTER (WHERE event_type = 'home') AS home_events_count,
    COUNT(*) FILTER (WHERE event_type = 'department') AS department_events_count,
    COUNT(*) FILTER (WHERE event_type = 'product') AS product_events_count,
    COUNT(*) FILTER (WHERE event_type = 'cart') AS cart_events_count,
    COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchase_events_count,
    COUNT(*) FILTER (WHERE event_type = 'cancel') AS cancel_events_count,
    CURRENT_DATE - MAX(created_at)::date AS days_since_last_event
FROM clean.events
WHERE user_id IS NOT NULL
GROUP BY 1
ORDER BY user_id;

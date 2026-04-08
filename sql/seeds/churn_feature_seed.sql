-- DEV/DEMO SEED — NOT FOR PRODUCTION USE
-- Creates and seeds the feature.churn table so that the churn happy-path request can succeed.
--
-- Ownership note: the `feature` schema is created by Alembic migrations (apps/backend).
-- This file only adds dev/demo DDL + data that is NOT part of the production migration path.
-- Do not use this file to manage production feature tables.
--
-- The feature.churn table schema is derived from ChurnFeatures in apps/ml_api and from the
-- primary query in apps/ml_api/app/infrastructure/repositories/features/churn_pg.py.
-- Columns must cover the fields expected by that query and by ChurnFeatures (numeric fields only
-- for the ML feature vector; rfm_segment is present for top_factors logic but is not in the
-- feature_columns.json vector).

BEGIN;

CREATE TABLE IF NOT EXISTS feature.churn (
    user_id               TEXT        PRIMARY KEY,
    days_since_last_order FLOAT,
    orders_count          FLOAT,
    total_revenue         FLOAT,
    recency_score         FLOAT,
    frequency_score       FLOAT,
    monetary_score        FLOAT,
    rfm_score             FLOAT,
    rfm_segment           TEXT,
    event_count           FLOAT,
    session_count         FLOAT,
    days_since_last_event FLOAT
);

-- Insert one demo user row used by the smoke-check script.
-- ON CONFLICT ensures idempotency.
INSERT INTO feature.churn (
    user_id,
    days_since_last_order,
    orders_count,
    total_revenue,
    recency_score,
    frequency_score,
    monetary_score,
    rfm_score,
    rfm_segment,
    event_count,
    session_count,
    days_since_last_event
) VALUES (
    'demo_user_001',
    45.0,
    3.0,
    120.50,
    2.0,
    2.0,
    3.0,
    7.0,
    'at_risk',
    12.0,
    5.0,
    20.0
)
ON CONFLICT (user_id) DO NOTHING;

COMMIT;

-- DEV/DEMO SEED — NOT FOR PRODUCTION USE
-- Inserts or updates one active churn model entry in the existing serving.model_registry table.
-- This table is owned by Alembic migrations (apps/backend). This file only seeds data.
-- Safe to re-run: uses INSERT ... ON CONFLICT DO UPDATE.

BEGIN;

-- Deactivate any other active rows for churn_model so there is exactly one active version.
UPDATE serving.model_registry
SET is_active = FALSE
WHERE model_name = 'churn_model'
  AND model_version != 'v1';

-- Insert the active churn model row, or update it if it already exists.
INSERT INTO serving.model_registry (model_name, model_version, stage, artifact_path, is_active)
VALUES ('churn_model', 'v1', 'production', 'churn_model/v1', TRUE)
ON CONFLICT (model_name, model_version)
DO UPDATE SET
    stage         = EXCLUDED.stage,
    artifact_path = EXCLUDED.artifact_path,
    is_active     = EXCLUDED.is_active;

COMMIT;

# Churn Happy-Path: Local Developer Guide

This document explains how to run the churn prediction use case end-to-end in the local Docker Compose stack.

> **These scripts and seeds are dev/demo-only.**
> They are not part of the production deployment path and must not be used to manage production databases.

---

## Prerequisites

- Docker and Docker Compose installed and running.
- A `.env` file exists at the project root.  
  The file must define at minimum: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_DSN`, `ML_API_PORT`.  
  The default `.env` in this repository already has these values for local development.

---

## One-command bootstrap

From the project root, run:

```bash
./scripts/bootstrap_churn_happy_path.sh
```

This script performs the following steps in order:

1. Starts `postgres` and `redis` services.
2. Runs the `migrator` service to apply all Alembic migrations (creates schemas and the `serving.model_registry` table).
3. Applies the churn registry seed — inserts one active `churn_model/v1` row into `serving.model_registry`.
4. Applies the churn feature seed — creates `feature.churn` (if it does not exist) and inserts a demo user row.
5. Generates churn demo model artifacts inside the `ml-api` container — writes a real sklearn `model.pkl` and `feature_columns.json` to `artifacts/models/churn_model/v1/`.
6. Starts (or restarts) the `ml-api` service.

The script is **safe to re-run**: all seeds use `ON CONFLICT DO NOTHING/UPDATE` and the artifact generator overwrites any existing stub.

---

## Smoke-check

After the bootstrap completes, verify the churn happy-path:

```bash
./scripts/smoke_check_churn.sh
```

This checks:

1. `GET /ml/health` returns `{"status": "ok", ...}`.
2. `GET /ml/ready` returns `{"status": "ready", ...}` (HTTP 200).
3. `POST /ml/churn/predict` with `{"user_id": "demo_user_001"}` returns a successful prediction response.

The script exits with a non-zero status code if any check fails.

Override the port if needed:

```bash
ML_API_PORT=18001 ./scripts/smoke_check_churn.sh
```

---

## What the churn request looks like

```bash
curl -s \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user_001"}' \
  http://localhost:18001/ml/churn/predict | python -m json.tool
```

Expected response shape (actual probability will vary):

```json
{
  "status": "ok",
  "request_type": "churn",
  "todo": "",
  "payload": {
    "churn_probability": 0.72,
    "churn_bucket": "high",
    "top_factors": [
      {"feature": "days_since_last_order", "direction": "risk_up"},
      {"feature": "rfm_segment", "direction": "risk_up"},
      {"feature": "days_since_last_event", "direction": "risk_up"}
    ]
  },
  "trace_payload": null
}
```

---

## Files added by this task

| File | Purpose |
|------|---------|
| `sql/seeds/churn_registry_seed.sql` | Dev/demo registry seed (idempotent) |
| `sql/seeds/churn_feature_seed.sql` | Dev/demo feature seed, includes minimal DDL for `feature.churn` (idempotent) |
| `apps/ml_api/scripts/generate_churn_demo_artifacts.py` | Generates real sklearn artifacts under `artifacts/models/churn_model/v1/` |
| `scripts/bootstrap_churn_happy_path.sh` | Orchestrates the full bootstrap sequence |
| `scripts/smoke_check_churn.sh` | End-to-end smoke-check |
| `docs/churn_happy_path.md` | This file |

No existing API contracts, Pydantic models, runtime code, or docker-compose services were changed.

---

## Troubleshooting

**`/ml/ready` returns 503 after bootstrap**

- Check `docker compose logs ml-api` for startup errors.
- Ensure the artifact generator ran successfully: `artifacts/models/churn_model/v1/model.pkl` and `feature_columns.json` must both exist.
- Ensure the registry seed was applied: `SELECT * FROM serving.model_registry WHERE model_name='churn_model';`

**Churn predict returns 404 for `demo_user_001`**

- Ensure the feature seed was applied: `SELECT * FROM feature.churn WHERE user_id='demo_user_001';`

**Port conflict**

- Check `ML_API_PORT` in `.env`. Default is `18001`.

#!/usr/bin/env bash
# DEV/DEMO SCRIPT — NOT FOR PRODUCTION USE.
#
# Bootstraps the churn happy-path in the local Docker Compose stack.
# Safe to re-run: all seeds are idempotent and the artifact generator overwrites stubs.
#
# Usage (from the project root):
#   ./scripts/bootstrap_churn_happy_path.sh
#
# Prerequisites:
#   - Docker and Docker Compose are installed and running.
#   - A .env file exists at the project root with POSTGRES_USER, POSTGRES_DB, etc.
#     (same .env used by docker compose).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Load DB credentials from .env so we can pass them to psql.
# Only load the variables we actually need; do not export the entire .env blindly.
if [[ -f .env ]]; then
    POSTGRES_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2 | tr -d '"' || true)
    POSTGRES_DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2 | tr -d '"' || true)
fi
POSTGRES_USER="${POSTGRES_USER:-retail}"
POSTGRES_DB="${POSTGRES_DB:-retail_analytics}"

echo "==> [1/6] Starting postgres and redis..."
docker compose up -d postgres redis

echo "==> [2/6] Waiting for postgres to be healthy..."
docker compose up -d postgres
# Wait until postgres reports healthy (compose up -d already waits for healthcheck via depends_on,
# but we also run migrator next which has its own healthcheck dependency).

echo "==> [3/6] Running migrator to apply all Alembic migrations..."
docker compose run --rm migrator

echo "==> [4/6] Applying churn registry seed..."
docker compose exec -T postgres psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    < sql/seeds/churn_registry_seed.sql

echo "==> [5/6] Applying churn feature seed..."
docker compose exec -T postgres psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    < sql/seeds/churn_feature_seed.sql

echo "==> [6a/6] Generating churn demo model artifacts inside the ml-api container..."
docker compose run --rm ml-api \
    python /workspace/apps/ml_api/scripts/generate_churn_demo_artifacts.py

echo "==> [6b/6] Starting (or restarting) ml-api..."
docker compose up -d ml-api

echo ""
echo "Bootstrap complete."
echo "Run './scripts/smoke_check_churn.sh' to verify the churn happy-path."

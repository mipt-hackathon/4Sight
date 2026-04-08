#!/usr/bin/env bash
# DEV/DEMO SCRIPT — NOT FOR PRODUCTION USE.
#
# Smoke-checks the churn happy-path against the running ml-api service.
# Exits with a non-zero status code if any check fails.
#
# Usage (from the project root):
#   ./scripts/smoke_check_churn.sh
#
# Override the port if needed:
#   ML_API_PORT=18001 ./scripts/smoke_check_churn.sh

set -euo pipefail

ML_API_PORT="${ML_API_PORT:-18001}"
BASE_URL="http://localhost:${ML_API_PORT}"

echo "==> Smoke-checking ml-api at ${BASE_URL}"
echo ""

# ---- 1. Health ----
echo "[1/3] GET /ml/health"
HEALTH_RESPONSE=$(curl -fsS "${BASE_URL}/ml/health")
echo "Response: ${HEALTH_RESPONSE}"
echo "${HEALTH_RESPONSE}" | grep -q '"status"' || { echo "FAIL: /ml/health did not return expected JSON"; exit 1; }
echo "PASS"
echo ""

# ---- 2. Readiness ----
echo "[2/3] GET /ml/ready"
READY_RESPONSE=$(curl -fsS "${BASE_URL}/ml/ready")
echo "Response: ${READY_RESPONSE}"
echo "${READY_RESPONSE}" | grep -q '"status": *"ready"' || { echo "FAIL: /ml/ready did not return status=ready"; exit 1; }
echo "PASS"
echo ""

# ---- 3. Churn prediction ----
echo "[3/3] POST /ml/churn/predict (user_id=demo_user_001)"
PREDICT_RESPONSE=$(curl -fsS \
    -H "Content-Type: application/json" \
    -d '{"user_id": "demo_user_001"}' \
    "${BASE_URL}/ml/churn/predict")
echo "Response: ${PREDICT_RESPONSE}"
echo "${PREDICT_RESPONSE}" | grep -q '"status": *"ok"' || { echo "FAIL: /ml/churn/predict did not return status=ok"; exit 1; }
echo "${PREDICT_RESPONSE}" | grep -q '"churn_probability"' || { echo "FAIL: /ml/churn/predict response missing churn_probability"; exit 1; }
echo "PASS"
echo ""

echo "All smoke-checks passed."

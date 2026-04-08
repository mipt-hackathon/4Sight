"""
DEV/DEMO SCRIPT — NOT FOR PRODUCTION USE.

Generates a minimal sklearn churn model artifact set that the ml_api runtime can load.

Expected artifact layout (matches registry seed artifact_path='churn_model/v1'):
  /workspace/artifacts/models/churn_model/v1/model.pkl          — sklearn model with predict_proba
  /workspace/artifacts/models/churn_model/v1/feature_columns.json — ordered list of feature names

Run inside the ml-api container:
  python /workspace/apps/ml_api/scripts/generate_churn_demo_artifacts.py

Or via docker compose from the project root:
  docker compose run --rm ml-api python /workspace/apps/ml_api/scripts/generate_churn_demo_artifacts.py
"""

import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

# Feature columns: numeric only, must match the order used in feature_columns.json.
# These are the same fields that RuntimeManagerImpl._build_input reads from ChurnFeatures
# (excluding user_id, rfm_segment, and any other non-numeric fields).
FEATURE_COLUMNS = [
    "days_since_last_order",
    "orders_count",
    "total_revenue",
    "recency_score",
    "frequency_score",
    "monetary_score",
    "event_count",
    "session_count",
    "days_since_last_event",
]

ARTIFACT_DIR = Path("/workspace/artifacts/models/churn_model/v1")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    n_features = len(FEATURE_COLUMNS)
    rng = np.random.default_rng(seed=42)

    # Synthetic training data: 200 samples, binary labels.
    X_train = rng.uniform(0, 100, size=(200, n_features))
    # Simple rule: churned if days_since_last_order > 50 or days_since_last_event > 60
    y_train = ((X_train[:, 0] > 50) | (X_train[:, 8] > 60)).astype(int)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train)

    model_path = ARTIFACT_DIR / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved model.pkl -> {model_path}")

    columns_path = ARTIFACT_DIR / "feature_columns.json"
    with open(columns_path, "w") as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)
    print(f"Saved feature_columns.json -> {columns_path}")

    # Quick sanity-check: run predict_proba on the demo user's values.
    demo_row = np.array([[45.0, 3.0, 120.50, 2.0, 2.0, 3.0, 12.0, 5.0, 20.0]])
    proba = float(model.predict_proba(demo_row)[0, 1])
    print(f"Sanity check — demo_user_001 churn probability: {proba:.4f}")
    print("Artifacts generated successfully.")


if __name__ == "__main__":
    main()

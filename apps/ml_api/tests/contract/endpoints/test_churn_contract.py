from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.dto.features import ChurnFeatures
from app.domain.dto.registry import ModelVersionInfo
from app.runtime.manager_impl import RuntimeManagerImpl
from tests.contract.conftest import make_test_app

_SAMPLE_VERSION = ModelVersionInfo(
    model_name="churn_model",
    model_version="v1",
    stage="production",
    artifact_path="churn_model/v1",
    is_active=True,
    created_at=datetime(2026, 1, 1),
)

_SAMPLE_FEATURES = ChurnFeatures(
    user_id="u1",
    days_since_last_order=45.0,
    orders_count=3.0,
    total_revenue=120.0,
    recency_score=2.0,
    frequency_score=3.0,
    monetary_score=4.0,
    event_count=10.0,
    session_count=5.0,
    days_since_last_event=20.0,
)


def make_runtime():
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.2, 0.8]])
    runtime.register("churn_model", model, ["days_since_last_order", "orders_count"])
    return runtime


def make_state(feature_repo=None, registry_repo=None, runtime=None, resolver=None):
    if runtime is None:
        runtime = make_runtime()
    if feature_repo is None:
        feature_repo = MagicMock()
        feature_repo.get_features_for_user.return_value = _SAMPLE_FEATURES
    if registry_repo is None:
        registry_repo = MagicMock()
        registry_repo.get_active_model_version.return_value = _SAMPLE_VERSION
    if resolver is None:
        resolver = MagicMock()
        resolver.resolve.return_value = "churn_model"
    return {
        "db_engine": MagicMock(),
        "runtime": runtime,
        "resolver": resolver,
        "registry_repo": registry_repo,
        "_churn_feature_repo": feature_repo,
    }


@pytest.fixture
def client():
    state = make_state()
    app = make_test_app(state)

    # Patch the container to return our mock feature repo
    feature_repo = state["_churn_feature_repo"]
    with patch(
        "app.dependencies.container.ChurnFeatureRepositoryImpl",
        return_value=feature_repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_churn_predict_valid_request(client):
    resp = client.post("/ml/churn/predict", json={"user_id": "u1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["request_type"] == "churn"
    assert body["todo"] == ""
    assert body["trace_payload"] is None
    payload = body["payload"]
    assert "churn_probability" in payload
    assert "churn_bucket" in payload
    assert payload["churn_bucket"] in ("low", "medium", "high")


def test_churn_predict_features_not_found():
    repo = MagicMock()
    repo.get_features_for_user.return_value = None
    state = make_state(feature_repo=repo)
    app = make_test_app(state)
    with patch(
        "app.dependencies.container.ChurnFeatureRepositoryImpl",
        return_value=repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/ml/churn/predict", json={"user_id": "missing"})
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "error"
    assert body["payload"]["error_code"] == "FEATURES_NOT_FOUND"


def test_churn_predict_no_active_model():
    registry = MagicMock()
    registry.get_active_model_version.return_value = None
    state = make_state(registry_repo=registry)
    app = make_test_app(state)
    feature_repo = state["_churn_feature_repo"]
    with patch(
        "app.dependencies.container.ChurnFeatureRepositoryImpl",
        return_value=feature_repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/ml/churn/predict", json={"user_id": "u1"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["payload"]["error_code"] == "NO_ACTIVE_MODEL"


def test_churn_predict_with_as_of_date(client):
    resp = client.post("/ml/churn/predict", json={"user_id": "u1", "as_of_date": "2026-01-01"})
    assert resp.status_code == 200


def test_churn_predict_missing_user_id(client):
    resp = client.post("/ml/churn/predict", json={})
    assert resp.status_code == 422

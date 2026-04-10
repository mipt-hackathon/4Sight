from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.dto.features import RecommendationsUserFeatures
from app.domain.dto.registry import ModelVersionInfo
from app.runtime.manager_impl import RuntimeManagerImpl
from tests.contract.conftest import make_test_app

_SAMPLE_VERSION = ModelVersionInfo(
    model_name="recsys_model",
    model_version="v1",
    stage="production",
    artifact_path="recsys_model/v1",
    is_active=True,
    created_at=datetime(2026, 1, 1),
)

_SAMPLE_FEATURES = RecommendationsUserFeatures(
    user_id="u1",
    orders_count=5.0,
    total_revenue=300.0,
    days_since_last_order=10.0,
    recency_score=4.0,
    frequency_score=4.0,
    monetary_score=4.0,
)


def make_runtime():
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict.return_value = np.array([[0.9, 0.85, 0.7, 0.6, 0.5]])
    runtime.register("recsys_model", model, ["orders_count", "total_revenue"])
    return runtime


def make_state(feature_repo=None, registry_repo=None, runtime=None, resolver=None):
    if runtime is None:
        runtime = make_runtime()
    if feature_repo is None:
        feature_repo = MagicMock()
        feature_repo.get_user_features.return_value = _SAMPLE_FEATURES
    if registry_repo is None:
        registry_repo = MagicMock()
        registry_repo.get_active_model_version.return_value = _SAMPLE_VERSION
    if resolver is None:
        resolver = MagicMock()
        resolver.resolve.return_value = "recsys_model"
    return {
        "db_engine": MagicMock(),
        "runtime": runtime,
        "resolver": resolver,
        "registry_repo": registry_repo,
        "_recs_feature_repo": feature_repo,
    }


@pytest.fixture
def client():
    state = make_state()
    app = make_test_app(state)
    feature_repo = state["_recs_feature_repo"]
    with patch(
        "app.dependencies.container.RecommendationsFeatureRepositoryImpl",
        return_value=feature_repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_recommendations_predict_valid_request(client):
    resp = client.post("/ml/recommendations/predict", json={"user_id": "u1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["request_type"] == "recommendations"
    assert body["todo"] == ""
    assert body["trace_payload"] is None
    payload = body["payload"]
    assert "items" in payload
    assert isinstance(payload["items"], list)


def test_recommendations_predict_features_not_found():
    repo = MagicMock()
    repo.get_user_features.return_value = None
    state = make_state(feature_repo=repo)
    app = make_test_app(state)
    with patch(
        "app.dependencies.container.RecommendationsFeatureRepositoryImpl",
        return_value=repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/ml/recommendations/predict", json={"user_id": "missing"})
    assert resp.status_code == 404
    assert resp.json()["payload"]["error_code"] == "FEATURES_NOT_FOUND"


def test_recommendations_predict_respects_limit(client):
    resp = client.post("/ml/recommendations/predict", json={"user_id": "u1", "limit": 2})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    assert len(payload["items"]) <= 2


def test_recommendations_predict_missing_user_id(client):
    resp = client.post("/ml/recommendations/predict", json={})
    assert resp.status_code == 422

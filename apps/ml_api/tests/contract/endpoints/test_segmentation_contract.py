from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.dto.features import SegmentationFeatures
from app.domain.dto.registry import ModelVersionInfo
from app.runtime.manager_impl import RuntimeManagerImpl
from tests.contract.conftest import make_test_app

_SAMPLE_VERSION = ModelVersionInfo(
    model_name="segmentation_model",
    model_version="v1",
    stage="production",
    artifact_path="segmentation_model/v1",
    is_active=True,
    created_at=datetime(2026, 1, 1),
)

_SAMPLE_FEATURES = SegmentationFeatures(
    user_id="u1",
    rfm_score=4.0,
    rfm_segment="high",
    recency_score=4.0,
    frequency_score=4.0,
    monetary_score=4.0,
)


def make_runtime(cluster_id=2):
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict.return_value = np.array([cluster_id])
    runtime.register("segmentation_model", model, ["rfm_score", "recency_score"])
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
        resolver.resolve.return_value = "segmentation_model"
    return {
        "db_engine": MagicMock(),
        "runtime": runtime,
        "resolver": resolver,
        "registry_repo": registry_repo,
        "_seg_feature_repo": feature_repo,
    }


@pytest.fixture
def client():
    state = make_state()
    app = make_test_app(state)
    feature_repo = state["_seg_feature_repo"]
    with patch(
        "app.dependencies.container.SegmentationFeatureRepositoryImpl",
        return_value=feature_repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_segmentation_predict_valid_request(client):
    resp = client.post("/ml/segmentation/predict", json={"user_id": "u1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["request_type"] == "segmentation"
    assert body["trace_payload"] is None
    payload = body["payload"]
    assert "segment" in payload
    assert isinstance(payload["segment"], str)


def test_segmentation_predict_features_not_found():
    repo = MagicMock()
    repo.get_features_for_user.return_value = None
    state = make_state(feature_repo=repo)
    app = make_test_app(state)
    with patch(
        "app.dependencies.container.SegmentationFeatureRepositoryImpl",
        return_value=repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/ml/segmentation/predict", json={"user_id": "missing"})
    assert resp.status_code == 404
    assert resp.json()["payload"]["error_code"] == "FEATURES_NOT_FOUND"


def test_segmentation_predict_missing_user_id(client):
    resp = client.post("/ml/segmentation/predict", json={})
    assert resp.status_code == 422


def test_segmentation_predict_payload_shape(client):
    resp = client.post("/ml/segmentation/predict", json={"user_id": "u1"})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    assert "segment" in payload
    if payload.get("details") is not None:
        assert "cluster_id" in payload["details"]

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.dto.features import ForecastHistory
from app.domain.dto.registry import ModelVersionInfo
from app.runtime.manager_impl import RuntimeManagerImpl
from tests.contract.conftest import make_test_app

_SAMPLE_VERSION = ModelVersionInfo(
    model_name="forecast_model",
    model_version="v1",
    stage="production",
    artifact_path="forecast_model/v1",
    is_active=True,
    created_at=datetime(2026, 1, 1),
)

_SAMPLE_HISTORY = ForecastHistory(
    entity_id="all",
    time_series=[{"date": "2026-04-01", "revenue": 12000.0}],
)


def make_runtime(horizon=30):
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict.return_value = np.array([[float(i * 1000) for i in range(horizon)]])
    runtime.register("forecast_model", model, ["num_rows"])
    return runtime


def make_state(feature_repo=None, registry_repo=None, runtime=None, resolver=None):
    if runtime is None:
        runtime = make_runtime()
    if feature_repo is None:
        feature_repo = MagicMock()
        feature_repo.get_timeseries_for_entity.return_value = _SAMPLE_HISTORY
    if registry_repo is None:
        registry_repo = MagicMock()
        registry_repo.get_active_model_version.return_value = _SAMPLE_VERSION
    if resolver is None:
        resolver = MagicMock()
        resolver.resolve.return_value = "forecast_model"
    return {
        "db_engine": MagicMock(),
        "runtime": runtime,
        "resolver": resolver,
        "registry_repo": registry_repo,
        "_forecast_feature_repo": feature_repo,
    }


@pytest.fixture
def client():
    state = make_state()
    app = make_test_app(state)
    feature_repo = state["_forecast_feature_repo"]
    with patch(
        "app.dependencies.container.ForecastFeatureRepositoryImpl",
        return_value=feature_repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_forecast_predict_valid_request(client):
    resp = client.post("/ml/forecast/predict", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["request_type"] == "forecast"
    assert body["trace_payload"] is None
    payload = body["payload"]
    assert "forecast" in payload
    assert isinstance(payload["forecast"], list)
    for point in payload["forecast"]:
        assert "date" in point
        assert "value" in point


def test_forecast_predict_features_not_found():
    repo = MagicMock()
    repo.get_timeseries_for_entity.return_value = None
    state = make_state(feature_repo=repo)
    app = make_test_app(state)
    with patch(
        "app.dependencies.container.ForecastFeatureRepositoryImpl",
        return_value=repo,
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/ml/forecast/predict", json={"entity_id": "missing"})
    assert resp.status_code == 404
    assert resp.json()["payload"]["error_code"] == "FEATURES_NOT_FOUND"


def test_forecast_predict_respects_horizon(client):
    resp = client.post("/ml/forecast/predict", json={"horizon_days": 7})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    assert len(payload["forecast"]) == 7

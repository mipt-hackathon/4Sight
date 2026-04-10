import pytest
from fastapi.testclient import TestClient

from app.runtime.manager_impl import RuntimeManagerImpl
from tests.contract.conftest import make_test_app

import numpy as np
from unittest.mock import MagicMock


def make_runtime_with_churn():
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.2, 0.8]])
    runtime.register("churn_model", model, ["col_a"])
    return runtime


def _base_state(runtime=None):
    if runtime is None:
        runtime = RuntimeManagerImpl()
    resolver = MagicMock()
    resolver.resolve.return_value = "churn_model"
    registry_repo = MagicMock()
    registry_repo.get_active_model_version.return_value = None
    return {
        "db_engine": MagicMock(),
        "runtime": runtime,
        "resolver": resolver,
        "registry_repo": registry_repo,
    }


@pytest.fixture
def client_no_models():
    app = make_test_app(_base_state())
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def client_with_models():
    runtime = make_runtime_with_churn()
    app = make_test_app(_base_state(runtime=runtime))
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_returns_ok(client_no_models):
    resp = client_no_models.get("/ml/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_returns_503_when_no_models(client_no_models):
    resp = client_no_models.get("/ml/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["loaded"] == []


def test_ready_returns_200_when_models_loaded(client_with_models):
    resp = client_with_models.get("/ml/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert "churn" in body["loaded"]

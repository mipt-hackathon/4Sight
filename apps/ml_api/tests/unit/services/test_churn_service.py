from datetime import date, datetime

import pytest

from app.application.services.churn_service import ChurnPredictionService
from app.domain.dto.features import ChurnFeatures
from app.domain.dto.registry import ModelVersionInfo
from app.domain.exceptions import FeaturesNotFoundError, NoActiveModelError


class MockChurnFeatureRepo:
    def __init__(self, features=None):
        self._features = features

    def get_features_for_user(self, user_id, as_of_date=None):
        return self._features


class MockModelRegistryRepo:
    def __init__(self, version_info=None):
        self._version_info = version_info

    def get_active_model_version(self, model_name):
        return self._version_info

    def list_model_versions(self, model_name):
        return []


class MockRuntime:
    def __init__(self, result=None):
        self._result = result or {"probability": 0.82}

    def predict_churn(self, features, options):
        return self._result

    def loaded_use_cases(self):
        return ["churn"]


class MockResolver:
    def resolve(self, use_case, model_key=None):
        return "churn_model"


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
    rfm_segment="low",
)

_SAMPLE_VERSION = ModelVersionInfo(
    model_name="churn_model",
    model_version="v1",
    stage="production",
    artifact_path="churn_model/v1",
    is_active=True,
    created_at=datetime(2026, 1, 1),
)


def make_service(**overrides):
    defaults = dict(
        feature_repo=MockChurnFeatureRepo(_SAMPLE_FEATURES),
        registry_repo=MockModelRegistryRepo(_SAMPLE_VERSION),
        runtime=MockRuntime(),
        resolver=MockResolver(),
    )
    defaults.update(overrides)
    return ChurnPredictionService(**defaults)


def test_predict_success_high_churn():
    service = make_service(runtime=MockRuntime({"probability": 0.82}))
    result = service.predict(user_id="u1")
    assert result.status == "ok"
    assert result.request_type == "churn"
    assert result.todo == ""
    assert result.trace_payload is None
    assert result.payload["churn_probability"] == pytest.approx(0.82)
    assert result.payload["churn_bucket"] == "high"


def test_predict_success_medium_churn():
    service = make_service(runtime=MockRuntime({"probability": 0.55}))
    result = service.predict(user_id="u1")
    assert result.payload["churn_bucket"] == "medium"


def test_predict_success_low_churn():
    service = make_service(runtime=MockRuntime({"probability": 0.2}))
    result = service.predict(user_id="u1")
    assert result.payload["churn_bucket"] == "low"
    assert result.payload["top_factors"] is None


def test_predict_features_not_found():
    service = make_service(feature_repo=MockChurnFeatureRepo(None))
    with pytest.raises(FeaturesNotFoundError):
        service.predict(user_id="u1")


def test_predict_no_active_model():
    service = make_service(registry_repo=MockModelRegistryRepo(None))
    with pytest.raises(NoActiveModelError):
        service.predict(user_id="u1")


def test_predict_with_as_of_date():
    service = make_service()
    result = service.predict(user_id="u1", as_of_date=date(2026, 1, 1))
    assert result.status == "ok"

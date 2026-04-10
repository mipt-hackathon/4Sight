import pytest

from app.infrastructure.resolvers.static_model_name import StaticModelNameResolver


def test_resolve_known_use_cases():
    resolver = StaticModelNameResolver()
    assert resolver.resolve("churn") == "churn_model"
    assert resolver.resolve("recommendations") == "recsys_model"
    assert resolver.resolve("forecast") == "forecast_model"
    assert resolver.resolve("segmentation") == "segmentation_model"


def test_resolve_unknown_use_case_raises():
    resolver = StaticModelNameResolver()
    with pytest.raises(ValueError, match="Unknown use case"):
        resolver.resolve("unknown_use_case")


def test_resolve_model_key_ignored():
    resolver = StaticModelNameResolver()
    assert resolver.resolve("churn", model_key="some_key") == "churn_model"

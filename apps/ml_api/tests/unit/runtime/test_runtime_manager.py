import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.domain.exceptions import ModelRuntimeError, NoActiveModelError
from app.runtime.manager_impl import RuntimeManagerImpl


def make_fake_classifier(proba=0.75):
    """Create a real sklearn-like mock with predict_proba."""
    model = MagicMock()
    model.predict_proba.return_value = np.array([[1 - proba, proba]])
    return model


def make_fake_predictor(output=None):
    model = MagicMock()
    model.predict.return_value = np.array(output if output is not None else [0])
    return model


def test_loaded_use_cases_empty():
    runtime = RuntimeManagerImpl()
    assert runtime.loaded_use_cases() == []


def test_register_and_loaded_use_cases():
    runtime = RuntimeManagerImpl()
    runtime.register("churn_model", make_fake_classifier(), ["col_a", "col_b"])
    loaded = runtime.loaded_use_cases()
    assert "churn" in loaded


def test_predict_churn_success():
    runtime = RuntimeManagerImpl()
    model = make_fake_classifier(proba=0.9)
    runtime.register("churn_model", model, ["col_a", "col_b"])
    result = runtime.predict_churn({"col_a": 1.0, "col_b": 2.0}, None)
    assert "probability" in result
    assert result["probability"] == pytest.approx(0.9)


def test_predict_churn_no_model_raises():
    runtime = RuntimeManagerImpl()
    with pytest.raises(NoActiveModelError):
        runtime.predict_churn({"col_a": 1.0}, None)


def test_predict_churn_model_error():
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    model.predict_proba.side_effect = RuntimeError("model exploded")
    runtime.register("churn_model", model, ["col_a"])
    with pytest.raises(ModelRuntimeError):
        runtime.predict_churn({"col_a": 1.0}, None)


def test_predict_segmentation_success():
    runtime = RuntimeManagerImpl()
    model = make_fake_predictor([2])
    runtime.register("segmentation_model", model, ["rfm_score"])
    result = runtime.predict_segmentation({"rfm_score": 3.0}, None)
    assert result["cluster_id"] == 2


def test_feature_columns_used_in_order():
    runtime = RuntimeManagerImpl()
    model = MagicMock()
    captured = []

    def capture_proba(X):
        captured.append(X.tolist())
        return np.array([[0.3, 0.7]])

    model.predict_proba.side_effect = capture_proba
    runtime.register("churn_model", model, ["b", "a"])

    runtime.predict_churn({"a": 10.0, "b": 20.0}, None)
    assert captured[0][0] == [20.0, 10.0]

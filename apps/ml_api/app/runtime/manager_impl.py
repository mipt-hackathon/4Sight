import logging
from typing import Any

import numpy as np

from app.api.schemas.base import ModelRoutingOptions
from app.domain.exceptions import ModelRuntimeError, NoActiveModelError

logger = logging.getLogger(__name__)

_USE_CASE_TO_MODEL = {
    "churn": "churn_model",
    "recommendations": "recsys_model",
    "forecast": "forecast_model",
    "segmentation": "segmentation_model",
}


class RuntimeManagerImpl:
    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._feature_columns: dict[str, list[str]] = {}

    def register(self, model_name: str, model: Any, feature_columns: list[str]) -> None:
        self._models[model_name] = model
        self._feature_columns[model_name] = feature_columns
        logger.info("model_name=%s registered with %d feature columns", model_name, len(feature_columns))

    def loaded_use_cases(self) -> list[str]:
        return [uc for uc, mn in _USE_CASE_TO_MODEL.items() if mn in self._models]

    def _get_model(self, model_name: str, use_case: str) -> Any:
        model = self._models.get(model_name)
        if model is None:
            raise NoActiveModelError(use_case=use_case, model_name=model_name)
        return model

    def _build_input(self, features: dict[str, Any], model_name: str) -> np.ndarray:
        cols = self._feature_columns[model_name]
        row = [float(features.get(c) or 0.0) for c in cols]
        return np.array([row])

    def predict_churn(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]:
        model_name = "churn_model"
        try:
            model = self._get_model(model_name, "churn")
            X = self._build_input(features, model_name)
            proba = float(model.predict_proba(X)[0, 1])
            return {"probability": proba}
        except NoActiveModelError:
            raise
        except Exception as exc:
            raise ModelRuntimeError(use_case="churn", cause=exc) from exc

    def predict_recommendations(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]:
        model_name = "recsys_model"
        try:
            model = self._get_model(model_name, "recommendations")
            X = self._build_input(features, model_name)
            scores = model.predict(X)
            items = [
                {"item_id": str(i), "score": float(s), "reason": None}
                for i, s in enumerate(scores[0])
            ]
            return {"items": items}
        except NoActiveModelError:
            raise
        except Exception as exc:
            raise ModelRuntimeError(use_case="recommendations", cause=exc) from exc

    def predict_forecast(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]:
        model_name = "forecast_model"
        try:
            model = self._get_model(model_name, "forecast")
            X = self._build_input(features, model_name)
            forecast_values = model.predict(X)
            return {"forecast_values": [float(v) for v in forecast_values[0]]}
        except NoActiveModelError:
            raise
        except Exception as exc:
            raise ModelRuntimeError(use_case="forecast", cause=exc) from exc

    def predict_segmentation(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]:
        model_name = "segmentation_model"
        try:
            model = self._get_model(model_name, "segmentation")
            X = self._build_input(features, model_name)
            cluster_id = int(model.predict(X)[0])
            return {"cluster_id": cluster_id}
        except NoActiveModelError:
            raise
        except Exception as exc:
            raise ModelRuntimeError(use_case="segmentation", cause=exc) from exc

import logging
import time
from datetime import date, timedelta
from typing import Any

from app.api.schemas.base import ModelRoutingOptions, StubPredictionResponse
from app.api.schemas.forecast import ForecastPayload, ForecastPoint
from app.domain.dto.features import ForecastHistory
from app.domain.exceptions import FeaturesNotFoundError, NoActiveModelError
from app.domain.repositories.features import ForecastFeatureRepository
from app.domain.repositories.model_registry import ModelRegistryRepository
from app.domain.runtime.manager import ModelNameResolver, RuntimeManager

logger = logging.getLogger(__name__)

_USE_CASE = "forecast"


class ForecastService:
    def __init__(
        self,
        feature_repo: ForecastFeatureRepository,
        registry_repo: ModelRegistryRepository,
        runtime: RuntimeManager,
        resolver: ModelNameResolver,
    ) -> None:
        self._feature_repo = feature_repo
        self._registry_repo = registry_repo
        self._runtime = runtime
        self._resolver = resolver

    def predict(self, entity_id: str = "all", horizon_days: int = 30) -> StubPredictionResponse:
        t0 = time.monotonic()

        history = self._feature_repo.get_timeseries_for_entity(entity_id)
        if history is None:
            raise FeaturesNotFoundError(use_case=_USE_CASE, key=entity_id)

        model_name = self._resolver.resolve(_USE_CASE)
        version_info = self._registry_repo.get_active_model_version(model_name)
        if version_info is None:
            raise NoActiveModelError(use_case=_USE_CASE, model_name=model_name)

        features_dict = self._build_features_dict(history)
        options: ModelRoutingOptions | None = None
        raw = self._runtime.predict_forecast(features_dict, options)

        forecast_values = raw.get("forecast_values", [])
        today = date.today()
        forecast_points = [
            ForecastPoint(date=today + timedelta(days=i + 1), value=v)
            for i, v in enumerate(forecast_values[:horizon_days])
        ]

        if not forecast_points:
            for i in range(horizon_days):
                forecast_points.append(ForecastPoint(date=today + timedelta(days=i + 1), value=0.0))

        payload_model = ForecastPayload(forecast=forecast_points)

        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.info("use_case=%s latency_ms=%d outcome=success", _USE_CASE, latency_ms)

        return StubPredictionResponse(
            status="ok",
            request_type=_USE_CASE,
            todo="",
            payload=payload_model.model_dump(),
            trace_payload=None,
        )

    def _build_features_dict(self, history: ForecastHistory) -> dict[str, Any]:
        return {
            "entity_id": history.entity_id,
            "num_rows": len(history.time_series),
        }

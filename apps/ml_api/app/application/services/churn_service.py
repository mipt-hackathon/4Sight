import logging
import time
from datetime import date
from typing import Any

from app.api.schemas.base import ModelRoutingOptions, StubPredictionResponse
from app.api.schemas.churn import ChurnPredictionPayload, TopFactor
from app.domain.dto.features import ChurnFeatures
from app.domain.exceptions import FeaturesNotFoundError, NoActiveModelError
from app.domain.repositories.features import ChurnFeatureRepository
from app.domain.repositories.model_registry import ModelRegistryRepository
from app.domain.runtime.manager import ModelNameResolver, RuntimeManager

logger = logging.getLogger(__name__)

_USE_CASE = "churn"


class ChurnPredictionService:
    def __init__(
        self,
        feature_repo: ChurnFeatureRepository,
        registry_repo: ModelRegistryRepository,
        runtime: RuntimeManager,
        resolver: ModelNameResolver,
    ) -> None:
        self._feature_repo = feature_repo
        self._registry_repo = registry_repo
        self._runtime = runtime
        self._resolver = resolver

    def predict(self, user_id: str, as_of_date: date | None = None) -> StubPredictionResponse:
        t0 = time.monotonic()

        features = self._feature_repo.get_features_for_user(user_id, as_of_date)
        if features is None:
            raise FeaturesNotFoundError(use_case=_USE_CASE, key=user_id)

        model_name = self._resolver.resolve(_USE_CASE)
        version_info = self._registry_repo.get_active_model_version(model_name)
        if version_info is None:
            raise NoActiveModelError(use_case=_USE_CASE, model_name=model_name)

        features_dict = self._build_features_dict(features)
        options: ModelRoutingOptions | None = None
        raw = self._runtime.predict_churn(features_dict, options)

        probability = float(raw["probability"])
        bucket = self._churn_bucket(probability)
        top_factors = self._top_factors(features, probability)

        payload_model = ChurnPredictionPayload(
            churn_probability=probability,
            churn_bucket=bucket,
            top_factors=top_factors,
        )

        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.info("use_case=%s latency_ms=%d outcome=success", _USE_CASE, latency_ms)

        return StubPredictionResponse(
            status="ok",
            request_type=_USE_CASE,
            todo="",
            payload=payload_model.model_dump(),
            trace_payload=None,
        )

    def _build_features_dict(self, features: ChurnFeatures) -> dict[str, Any]:
        return {k: v for k, v in features.model_dump().items() if k != "user_id"}

    @staticmethod
    def _churn_bucket(probability: float) -> str:
        if probability >= 0.7:
            return "high"
        if probability >= 0.4:
            return "medium"
        return "low"

    @staticmethod
    def _top_factors(features: ChurnFeatures, probability: float) -> list[TopFactor] | None:
        if probability < 0.4:
            return None
        candidates = []
        if features.days_since_last_order is not None and features.days_since_last_order > 30:
            candidates.append(TopFactor(feature="days_since_last_order", direction="risk_up"))
        if features.rfm_segment is not None:
            candidates.append(TopFactor(feature="rfm_segment", direction="risk_up"))
        if features.days_since_last_event is not None and features.days_since_last_event > 14:
            candidates.append(TopFactor(feature="days_since_last_event", direction="risk_up"))
        return candidates or None

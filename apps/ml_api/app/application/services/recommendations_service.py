import logging
import time
from typing import Any

from app.api.schemas.base import ModelRoutingOptions, StubPredictionResponse
from app.api.schemas.recommendations import RecommendationItem, RecommendationsPayload
from app.domain.dto.features import RecommendationsUserFeatures
from app.domain.exceptions import FeaturesNotFoundError, NoActiveModelError
from app.domain.repositories.features import RecommendationsFeatureRepository
from app.domain.repositories.model_registry import ModelRegistryRepository
from app.domain.runtime.manager import ModelNameResolver, RuntimeManager

logger = logging.getLogger(__name__)

_USE_CASE = "recommendations"


class RecommendationsService:
    def __init__(
        self,
        feature_repo: RecommendationsFeatureRepository,
        registry_repo: ModelRegistryRepository,
        runtime: RuntimeManager,
        resolver: ModelNameResolver,
    ) -> None:
        self._feature_repo = feature_repo
        self._registry_repo = registry_repo
        self._runtime = runtime
        self._resolver = resolver

    def predict(self, user_id: str, limit: int = 5) -> StubPredictionResponse:
        t0 = time.monotonic()

        features = self._feature_repo.get_user_features(user_id)
        if features is None:
            raise FeaturesNotFoundError(use_case=_USE_CASE, key=user_id)

        model_name = self._resolver.resolve(_USE_CASE)
        version_info = self._registry_repo.get_active_model_version(model_name)
        if version_info is None:
            raise NoActiveModelError(use_case=_USE_CASE, model_name=model_name)

        features_dict = self._build_features_dict(features)
        options: ModelRoutingOptions | None = None
        raw = self._runtime.predict_recommendations(features_dict, options)

        raw_items = raw.get("items", [])[:limit]
        items = [
            RecommendationItem(
                item_id=item["item_id"],
                score=item.get("score"),
                reason=item.get("reason"),
            )
            for item in raw_items
        ]

        payload_model = RecommendationsPayload(items=items)

        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.info("use_case=%s latency_ms=%d outcome=success", _USE_CASE, latency_ms)

        return StubPredictionResponse(
            status="ok",
            request_type=_USE_CASE,
            todo="",
            payload=payload_model.model_dump(),
            trace_payload=None,
        )

    def _build_features_dict(self, features: RecommendationsUserFeatures) -> dict[str, Any]:
        return {k: v for k, v in features.model_dump().items() if k != "user_id"}

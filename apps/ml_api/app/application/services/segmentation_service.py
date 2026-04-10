import logging
import time
from typing import Any

from app.api.schemas.base import ModelRoutingOptions, StubPredictionResponse
from app.api.schemas.segmentation import SegmentationDetails, SegmentationPayload
from app.domain.dto.features import SegmentationFeatures
from app.domain.exceptions import FeaturesNotFoundError, NoActiveModelError
from app.domain.repositories.features import SegmentationFeatureRepository
from app.domain.repositories.model_registry import ModelRegistryRepository
from app.domain.runtime.manager import ModelNameResolver, RuntimeManager

logger = logging.getLogger(__name__)

_USE_CASE = "segmentation"

_SEGMENT_LABELS: dict[int, str] = {
    0: "low_value",
    1: "medium_value",
    2: "high_value_loyal",
    3: "high_value_at_risk",
    4: "new_customer",
}


class SegmentationService:
    def __init__(
        self,
        feature_repo: SegmentationFeatureRepository,
        registry_repo: ModelRegistryRepository,
        runtime: RuntimeManager,
        resolver: ModelNameResolver,
    ) -> None:
        self._feature_repo = feature_repo
        self._registry_repo = registry_repo
        self._runtime = runtime
        self._resolver = resolver

    def predict(self, user_id: str, segment_scope: str = "customer") -> StubPredictionResponse:
        t0 = time.monotonic()

        features = self._feature_repo.get_features_for_user(user_id)
        if features is None:
            raise FeaturesNotFoundError(use_case=_USE_CASE, key=user_id)

        model_name = self._resolver.resolve(_USE_CASE)
        version_info = self._registry_repo.get_active_model_version(model_name)
        if version_info is None:
            raise NoActiveModelError(use_case=_USE_CASE, model_name=model_name)

        features_dict = self._build_features_dict(features)
        options: ModelRoutingOptions | None = None
        raw = self._runtime.predict_segmentation(features_dict, options)

        cluster_id = raw.get("cluster_id", 0)
        segment = _SEGMENT_LABELS.get(cluster_id, f"cluster_{cluster_id}")

        details = SegmentationDetails(
            rfm_code=features.rfm_segment,
            cluster_id=cluster_id,
        )
        payload_model = SegmentationPayload(segment=segment, details=details)

        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.info("use_case=%s latency_ms=%d outcome=success", _USE_CASE, latency_ms)

        return StubPredictionResponse(
            status="ok",
            request_type=_USE_CASE,
            todo="",
            payload=payload_model.model_dump(),
            trace_payload=None,
        )

    def _build_features_dict(self, features: SegmentationFeatures) -> dict[str, Any]:
        return {k: v for k, v in features.model_dump().items() if k != "user_id"}

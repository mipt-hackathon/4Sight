from datetime import date
from typing import Protocol

from app.domain.dto.features import (
    ChurnFeatures,
    ForecastHistory,
    RecommendationsUserFeatures,
    SegmentationFeatures,
)


class ChurnFeatureRepository(Protocol):
    def get_features_for_user(
        self, user_id: str, as_of_date: date | None = None
    ) -> ChurnFeatures | None: ...


class RecommendationsFeatureRepository(Protocol):
    def get_user_features(self, user_id: str) -> RecommendationsUserFeatures | None: ...


class ForecastFeatureRepository(Protocol):
    def get_timeseries_for_entity(
        self, entity_id: str, history_window: int | None = None
    ) -> ForecastHistory | None: ...


class SegmentationFeatureRepository(Protocol):
    def get_features_for_user(self, user_id: str) -> SegmentationFeatures | None: ...

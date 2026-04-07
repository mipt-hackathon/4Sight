from typing import Any

from pydantic import BaseModel


class ChurnFeatures(BaseModel):
    model_config = {"extra": "allow"}

    user_id: str
    days_since_last_order: float | None = None
    orders_count: float | None = None
    total_revenue: float | None = None
    recency_score: float | None = None
    frequency_score: float | None = None
    monetary_score: float | None = None
    event_count: float | None = None
    session_count: float | None = None
    days_since_last_event: float | None = None
    # From mart.rfm fallback join
    rfm_score: float | None = None
    rfm_segment: str | None = None


class RecommendationsUserFeatures(BaseModel):
    model_config = {"extra": "allow"}

    user_id: str
    orders_count: float | None = None
    total_revenue: float | None = None
    days_since_last_order: float | None = None
    recency_score: float | None = None
    frequency_score: float | None = None
    monetary_score: float | None = None


class ForecastHistory(BaseModel):
    entity_id: str
    time_series: list[dict[str, Any]]


class SegmentationFeatures(BaseModel):
    model_config = {"extra": "allow"}

    user_id: str
    rfm_score: float | None = None
    rfm_segment: str | None = None
    recency_score: float | None = None
    frequency_score: float | None = None
    monetary_score: float | None = None

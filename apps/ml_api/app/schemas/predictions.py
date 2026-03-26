from typing import Any

from pydantic import BaseModel, Field


class ChurnPredictionRequest(BaseModel):
    user_id: str = Field(..., description="Customer identifier for churn scoring.")
    as_of_date: str | None = Field(default=None, description="Optional scoring date.")


class RecommendationPredictionRequest(BaseModel):
    user_id: str = Field(..., description="Customer identifier for recommendation ranking.")
    limit: int = Field(default=5, ge=1, le=50)


class ForecastPredictionRequest(BaseModel):
    entity_id: str = Field(default="all", description="Entity or slice to forecast.")
    horizon_days: int = Field(default=30, ge=1, le=365)


class SegmentationPredictionRequest(BaseModel):
    user_id: str | None = Field(default=None, description="Optional customer identifier.")
    segment_scope: str = Field(default="customer")


class StubPredictionResponse(BaseModel):
    status: str
    request_type: str
    todo: str
    payload: dict[str, Any]

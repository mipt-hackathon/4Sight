from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.api.schemas.base import BaseMLRequest


class ChurnPredictionRequest(BaseMLRequest):
    user_id: str
    as_of_date: date | None = None


class TopFactor(BaseModel):
    feature: str
    direction: str


class ChurnPredictionPayload(BaseModel):
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    churn_bucket: Literal["low", "medium", "high"]
    top_factors: list[TopFactor] | None = None

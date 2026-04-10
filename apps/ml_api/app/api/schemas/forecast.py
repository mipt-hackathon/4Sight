from datetime import date

from pydantic import BaseModel, Field

from app.api.schemas.base import BaseMLRequest


class ForecastRequest(BaseMLRequest):
    entity_id: str = "all"
    horizon_days: int = Field(default=30, ge=1, le=365)


class ForecastPoint(BaseModel):
    date: date
    value: float


class ForecastPayload(BaseModel):
    forecast: list[ForecastPoint]

from pydantic import BaseModel, Field

from app.api.schemas.base import BaseMLRequest


class RecommendationsRequest(BaseMLRequest):
    user_id: str
    limit: int = Field(default=5, ge=1, le=50)


class RecommendationItem(BaseModel):
    item_id: str
    score: float | None = None
    reason: str | None = None


class RecommendationsPayload(BaseModel):
    items: list[RecommendationItem]

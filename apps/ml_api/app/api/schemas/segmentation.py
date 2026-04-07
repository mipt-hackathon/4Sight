from typing import Literal

from pydantic import BaseModel

from app.api.schemas.base import BaseMLRequest


class SegmentationRequest(BaseMLRequest):
    user_id: str
    segment_scope: Literal["customer"] = "customer"


class SegmentationDetails(BaseModel):
    rfm_code: str | None = None
    cluster_id: int | None = None


class SegmentationPayload(BaseModel):
    segment: str
    details: SegmentationDetails | None = None

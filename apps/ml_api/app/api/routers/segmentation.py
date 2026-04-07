import logging

from fastapi import APIRouter, Depends

from app.api.schemas.base import StubPredictionResponse
from app.api.schemas.segmentation import SegmentationRequest
from app.application.services.segmentation_service import SegmentationService
from app.dependencies.container import get_segmentation_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ml/segmentation/predict", response_model=StubPredictionResponse)
def predict_segmentation(
    request: SegmentationRequest,
    service: SegmentationService = Depends(get_segmentation_service),
) -> StubPredictionResponse:
    return service.predict(user_id=request.user_id, segment_scope=request.segment_scope)

import logging

from fastapi import APIRouter, Depends

from app.api.schemas.base import StubPredictionResponse
from app.api.schemas.recommendations import RecommendationsRequest
from app.application.services.recommendations_service import RecommendationsService
from app.dependencies.container import get_recommendations_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ml/recommendations/predict", response_model=StubPredictionResponse)
def predict_recommendations(
    request: RecommendationsRequest,
    service: RecommendationsService = Depends(get_recommendations_service),
) -> StubPredictionResponse:
    return service.predict(user_id=request.user_id, limit=request.limit)

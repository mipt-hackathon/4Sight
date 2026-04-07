import logging

from fastapi import APIRouter, Depends

from app.api.schemas.base import StubPredictionResponse
from app.api.schemas.churn import ChurnPredictionRequest
from app.application.services.churn_service import ChurnPredictionService
from app.dependencies.container import get_churn_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ml/churn/predict", response_model=StubPredictionResponse)
def predict_churn(
    request: ChurnPredictionRequest,
    service: ChurnPredictionService = Depends(get_churn_service),
) -> StubPredictionResponse:
    return service.predict(user_id=request.user_id, as_of_date=request.as_of_date)

import logging

from fastapi import APIRouter, Depends

from app.api.schemas.base import StubPredictionResponse
from app.api.schemas.forecast import ForecastRequest
from app.application.services.forecast_service import ForecastService
from app.dependencies.container import get_forecast_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ml/forecast/predict", response_model=StubPredictionResponse)
def predict_forecast(
    request: ForecastRequest,
    service: ForecastService = Depends(get_forecast_service),
) -> StubPredictionResponse:
    return service.predict(entity_id=request.entity_id, horizon_days=request.horizon_days)

from fastapi import APIRouter, Depends, Query

from app.api.models import SalesForecastResponse
from app.dependencies import get_retail_app_service
from app.services.retail_app_service import RetailAppService

router = APIRouter()


@router.get("/forecast", response_model=SalesForecastResponse)
def sales_forecast(
    entity_id: str = Query(default="all"),
    horizon_days: int = Query(default=30, ge=1, le=90),
    service: RetailAppService = Depends(get_retail_app_service),
) -> SalesForecastResponse:
    return service.get_sales_forecast(entity_id=entity_id, horizon_days=horizon_days)

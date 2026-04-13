from fastapi import APIRouter, Depends

from app.api.models import DashboardOverviewResponse
from app.dependencies import get_retail_app_service
from app.services.retail_app_service import RetailAppService

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    service: RetailAppService = Depends(get_retail_app_service),
) -> DashboardOverviewResponse:
    return service.get_dashboard_overview()

from fastapi import APIRouter, Depends

from app.api.models import SegmentsResponse
from app.dependencies import get_retail_app_service
from app.services.retail_app_service import RetailAppService

router = APIRouter()


@router.get("/segments", response_model=SegmentsResponse)
def list_segments(
    service: RetailAppService = Depends(get_retail_app_service),
) -> SegmentsResponse:
    return service.get_segments_summary()

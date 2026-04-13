from fastapi import APIRouter, Depends, Query

from app.api.models import RetentionTargetsResponse
from app.dependencies import get_retail_app_service
from app.services.retail_app_service import RetailAppService

router = APIRouter()


@router.get("/retention-targets", response_model=RetentionTargetsResponse)
def list_retention_targets(
    limit: int = Query(default=10, ge=1, le=30),
    per_user: int = Query(default=3, ge=1, le=10),
    service: RetailAppService = Depends(get_retail_app_service),
) -> RetentionTargetsResponse:
    return service.get_retention_targets(limit=limit, per_user=per_user)

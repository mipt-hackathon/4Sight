from fastapi import APIRouter, Depends, Query

from app.api.models import (
    CustomerChurnResponse,
    CustomerProfileResponse,
    CustomerRecommendationsResponse,
    CustomerSearchResponse,
    HighRiskCustomersResponse,
)
from app.dependencies import get_retail_app_service
from app.services.retail_app_service import RetailAppService

router = APIRouter()


@router.get("/search", response_model=CustomerSearchResponse)
def search_customers(
    q: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: RetailAppService = Depends(get_retail_app_service),
) -> CustomerSearchResponse:
    return service.search_customers(query=q, limit=limit)


@router.get("/high-risk", response_model=HighRiskCustomersResponse)
def list_high_risk_customers(
    limit: int = Query(default=20, ge=1, le=100),
    service: RetailAppService = Depends(get_retail_app_service),
) -> HighRiskCustomersResponse:
    return service.list_high_risk_customers(limit=limit)


@router.get("/{user_id}", response_model=CustomerProfileResponse)
def get_customer_profile(
    user_id: int,
    service: RetailAppService = Depends(get_retail_app_service),
) -> CustomerProfileResponse:
    return service.get_customer_profile(user_id)


@router.get("/{user_id}/churn", response_model=CustomerChurnResponse)
def get_customer_churn(
    user_id: int,
    service: RetailAppService = Depends(get_retail_app_service),
) -> CustomerChurnResponse:
    return service.get_customer_churn(user_id)


@router.get("/{user_id}/recommendations", response_model=CustomerRecommendationsResponse)
def get_customer_recommendations(
    user_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    service: RetailAppService = Depends(get_retail_app_service),
) -> CustomerRecommendationsResponse:
    return service.get_customer_recommendations(user_id, limit=limit)

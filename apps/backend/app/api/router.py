from fastapi import APIRouter

from app.api.routes.customers import router as customers_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.sales import router as sales_router
from app.api.routes.segments import router as segments_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
api_router.include_router(
    recommendations_router, prefix="/recommendations", tags=["recommendations"]
)
api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
api_router.include_router(segments_router, tags=["segments"])

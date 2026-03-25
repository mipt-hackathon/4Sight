from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.predictions import router as predictions_router

ml_router = APIRouter()
ml_router.include_router(health_router, tags=["health"])
ml_router.include_router(predictions_router, tags=["predictions"])

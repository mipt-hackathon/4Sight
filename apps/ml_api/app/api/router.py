from fastapi import APIRouter

from app.api.routes import health, predictions

ml_router = APIRouter()
ml_router.include_router(health.router, tags=["health"])
ml_router.include_router(predictions.router, tags=["predictions"])

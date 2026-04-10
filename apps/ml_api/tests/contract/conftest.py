"""Shared fixtures for contract tests.

Contract tests use a minimal FastAPI app without the real lifespan so they
can inject mock state (runtime, resolver, registry_repo) without a real DB.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers.churn import router as churn_router
from app.api.routers.forecast import router as forecast_router
from app.api.routers.health import router as health_router
from app.api.routers.recommendations import router as recommendations_router
from app.api.routers.segmentation import router as segmentation_router


def make_test_app(state: dict) -> FastAPI:
    """Create a FastAPI app with pre-wired mock state (no real lifespan)."""

    @asynccontextmanager
    async def test_lifespan(app: FastAPI) -> AsyncIterator[None]:
        for key, value in state.items():
            setattr(app.state, key, value)
        yield

    app = FastAPI(lifespan=test_lifespan)
    app.include_router(health_router, tags=["health"])
    app.include_router(churn_router, tags=["predictions"])
    app.include_router(recommendations_router, tags=["predictions"])
    app.include_router(forecast_router, tags=["predictions"])
    app.include_router(segmentation_router, tags=["predictions"])
    register_exception_handlers(app)
    return app

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from common.db.postgres import create_db_engine
from common.logging.setup import configure_logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_backend_settings
from app.repositories.analytics_repository import AnalyticsDataUnavailableError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_backend_settings()
    configure_logging(settings.app_log_level)

    app.state.db_engine = create_db_engine()
    app.state.ml_api_http_client = httpx.Client(
        base_url=settings.ml_api_base_url.rstrip("/"),
        timeout=settings.ml_api_timeout_seconds,
    )

    yield

    app.state.ml_api_http_client.close()
    app.state.db_engine.dispose()


def create_app() -> FastAPI:
    settings = get_backend_settings()
    cors_allowed_origins = [
        origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()
    ]

    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="Retail analytics product-facing backend.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(AnalyticsDataUnavailableError)
    async def analytics_data_unavailable_handler(
        request: Request,
        exc: AnalyticsDataUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error_code": "DATA_NOT_READY",
                "detail": str(exc),
                "path": str(request.url.path),
            },
        )

    application.include_router(api_router, prefix="/api")
    return application


app = create_app()

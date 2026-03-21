from common.logging import configure_logging
from fastapi import FastAPI

from app.api.router import ml_router
from app.core.config import get_ml_api_settings


def create_app() -> FastAPI:
    settings = get_ml_api_settings()
    configure_logging(settings.app_log_level)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Retail analytics ML API scaffold.",
    )
    application.include_router(ml_router)
    return application


app = create_app()

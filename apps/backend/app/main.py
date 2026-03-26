from common.logging.setup import configure_logging
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_backend_settings


def create_app() -> FastAPI:
    settings = get_backend_settings()
    configure_logging(settings.app_log_level)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Retail analytics backend scaffold.",
    )
    application.include_router(api_router, prefix="/api")
    return application


app = create_app()

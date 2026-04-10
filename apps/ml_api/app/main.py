import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from common.config.settings import get_settings
from common.db.postgres import create_db_engine
from common.logging.setup import configure_logging
from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers.churn import router as churn_router
from app.api.routers.forecast import router as forecast_router
from app.api.routers.health import router as health_router
from app.api.routers.recommendations import router as recommendations_router
from app.api.routers.segmentation import router as segmentation_router
from app.infrastructure.repositories.model_registry.registry_pg import ModelRegistryRepositoryImpl
from app.infrastructure.resolvers.static_model_name import StaticModelNameResolver
from app.runtime.loaders import load_feature_columns, load_pickle_artifact
from app.runtime.manager_impl import RuntimeManagerImpl

logger = logging.getLogger(__name__)

_KNOWN_USE_CASES = ["churn", "recommendations", "forecast", "segmentation"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.app_log_level)

    engine = create_db_engine()
    app.state.db_engine = engine

    resolver = StaticModelNameResolver()
    registry_repo = ModelRegistryRepositoryImpl(engine)
    runtime = RuntimeManagerImpl()

    logger.info("Startup: querying model registry for active models")
    for use_case in _KNOWN_USE_CASES:
        model_name = resolver.resolve(use_case)
        version_info = registry_repo.get_active_model_version(model_name)
        if version_info is None:
            logger.warning(
                "Startup: no active model use_case=%s model_name=%s", use_case, model_name
            )
            continue

        artifact_dir = settings.model_artifacts_path / version_info.artifact_path
        model_pkl = artifact_dir / "model.pkl"
        columns_json = artifact_dir / "feature_columns.json"

        try:
            t0 = time.monotonic()
            model = load_pickle_artifact(model_pkl)
            feature_columns = load_feature_columns(columns_json)
            load_time_ms = int((time.monotonic() - t0) * 1000)
            runtime.register(model_name, model, feature_columns)
            logger.info(
                "Startup: loaded model_name=%s model_version=%s artifact_path=%s "
                "num_columns=%d load_time_ms=%d",
                model_name,
                version_info.model_version,
                version_info.artifact_path,
                len(feature_columns),
                load_time_ms,
            )
        except FileNotFoundError as exc:
            logger.error(
                "Startup: artifact file missing model_name=%s path=%s", model_name, exc.filename
            )
        except Exception as exc:
            logger.error(
                "Startup: failed to load model_name=%s artifact_path=%s: %s",
                model_name,
                version_info.artifact_path,
                exc,
                exc_info=True,
            )

    app.state.runtime = runtime
    app.state.resolver = resolver
    app.state.registry_repo = registry_repo

    loaded = runtime.loaded_use_cases()
    if not loaded:
        logger.warning("Startup: no models loaded — all prediction endpoints will return 503")
    else:
        logger.info("Startup: loaded use cases: %s", loaded)

    yield

    engine.dispose()
    logger.info("Shutdown: database engine disposed")


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Retail Analytics ML API",
        lifespan=lifespan,
    )

    application.include_router(health_router, tags=["health"])
    application.include_router(churn_router, tags=["predictions"])
    application.include_router(recommendations_router, tags=["predictions"])
    application.include_router(forecast_router, tags=["predictions"])
    application.include_router(segmentation_router, tags=["predictions"])

    register_exception_handlers(application)

    return application


app = create_app()

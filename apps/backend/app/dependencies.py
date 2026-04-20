from fastapi import Depends, Request
from sqlalchemy.engine import Engine

from app.core.config import get_backend_settings
from app.integrations.ml_api_client import MlApiClient
from app.integrations.superset_client import SupersetClient
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.retail_app_service import RetailAppService
from app.services.superset_embed_service import SupersetEmbedService


def get_db_engine(request: Request) -> Engine:
    return request.app.state.db_engine


def get_analytics_repository(engine: Engine = Depends(get_db_engine)) -> AnalyticsRepository:
    return AnalyticsRepository(engine)


def get_ml_api_client(request: Request) -> MlApiClient:
    return MlApiClient(request.app.state.ml_api_http_client)


def get_superset_client(request: Request) -> SupersetClient:
    settings = get_backend_settings()
    return SupersetClient(
        request.app.state.superset_http_client,
        username=settings.superset_admin_username,
        password=settings.superset_admin_password,
    )


def get_superset_embed_service(
    superset_client: SupersetClient = Depends(get_superset_client),
) -> SupersetEmbedService:
    return SupersetEmbedService(
        superset_client=superset_client,
        settings=get_backend_settings(),
    )


def get_retail_app_service(
    repository: AnalyticsRepository = Depends(get_analytics_repository),
    ml_api_client: MlApiClient = Depends(get_ml_api_client),
) -> RetailAppService:
    return RetailAppService(repository=repository, ml_api_client=ml_api_client)

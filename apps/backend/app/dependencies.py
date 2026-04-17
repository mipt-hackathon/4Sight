from fastapi import Depends, Request
from sqlalchemy.engine import Engine

from app.integrations.ml_api_client import MlApiClient
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.retail_app_service import RetailAppService


def get_db_engine(request: Request) -> Engine:
    return request.app.state.db_engine


def get_analytics_repository(engine: Engine = Depends(get_db_engine)) -> AnalyticsRepository:
    return AnalyticsRepository(engine)


def get_ml_api_client(request: Request) -> MlApiClient:
    return MlApiClient(request.app.state.ml_api_http_client)


def get_retail_app_service(
    repository: AnalyticsRepository = Depends(get_analytics_repository),
    ml_api_client: MlApiClient = Depends(get_ml_api_client),
) -> RetailAppService:
    return RetailAppService(repository=repository, ml_api_client=ml_api_client)

from fastapi import Request

from app.application.services.churn_service import ChurnPredictionService
from app.application.services.forecast_service import ForecastService
from app.application.services.recommendations_service import RecommendationsService
from app.application.services.segmentation_service import SegmentationService
from app.infrastructure.repositories.features.churn_pg import ChurnFeatureRepositoryImpl
from app.infrastructure.repositories.features.forecast_pg import ForecastFeatureRepositoryImpl
from app.infrastructure.repositories.features.recommendations_pg import (
    RecommendationsFeatureRepositoryImpl,
)
from app.infrastructure.repositories.features.segmentation_pg import (
    SegmentationFeatureRepositoryImpl,
)


def get_churn_service(request: Request) -> ChurnPredictionService:
    engine = request.app.state.db_engine
    runtime = request.app.state.runtime
    resolver = request.app.state.resolver
    registry_repo = request.app.state.registry_repo
    return ChurnPredictionService(
        feature_repo=ChurnFeatureRepositoryImpl(engine),
        registry_repo=registry_repo,
        runtime=runtime,
        resolver=resolver,
    )


def get_recommendations_service(request: Request) -> RecommendationsService:
    engine = request.app.state.db_engine
    runtime = request.app.state.runtime
    resolver = request.app.state.resolver
    registry_repo = request.app.state.registry_repo
    return RecommendationsService(
        feature_repo=RecommendationsFeatureRepositoryImpl(engine),
        registry_repo=registry_repo,
        runtime=runtime,
        resolver=resolver,
    )


def get_forecast_service(request: Request) -> ForecastService:
    engine = request.app.state.db_engine
    runtime = request.app.state.runtime
    resolver = request.app.state.resolver
    registry_repo = request.app.state.registry_repo
    return ForecastService(
        feature_repo=ForecastFeatureRepositoryImpl(engine),
        registry_repo=registry_repo,
        runtime=runtime,
        resolver=resolver,
    )


def get_segmentation_service(request: Request) -> SegmentationService:
    engine = request.app.state.db_engine
    runtime = request.app.state.runtime
    resolver = request.app.state.resolver
    registry_repo = request.app.state.registry_repo
    return SegmentationService(
        feature_repo=SegmentationFeatureRepositoryImpl(engine),
        registry_repo=registry_repo,
        runtime=runtime,
        resolver=resolver,
    )

from fastapi import APIRouter

from app.schemas.predictions import (
    ChurnPredictionRequest,
    ForecastPredictionRequest,
    RecommendationPredictionRequest,
    SegmentationPredictionRequest,
    StubPredictionResponse,
)

router = APIRouter(prefix="/ml")


@router.post("/churn/predict", response_model=StubPredictionResponse)
def predict_churn(payload: ChurnPredictionRequest) -> StubPredictionResponse:
    # TODO: Load the churn model artifact and compute a real prediction.
    return StubPredictionResponse(
        status="stub",
        request_type="churn",
        todo="Implement churn model loading, feature lookup, and score explanation.",
        payload={"user_id": payload.user_id, "score": None},
    )


@router.post("/recommendations/predict", response_model=StubPredictionResponse)
def predict_recommendations(
    payload: RecommendationPredictionRequest,
) -> StubPredictionResponse:
    # TODO: Replace with actual recommendation ranking logic.
    return StubPredictionResponse(
        status="stub",
        request_type="recommendations",
        todo="Implement recsys feature retrieval and ranked product generation.",
        payload={"user_id": payload.user_id, "limit": payload.limit, "items": []},
    )


@router.post("/forecast/predict", response_model=StubPredictionResponse)
def predict_forecast(payload: ForecastPredictionRequest) -> StubPredictionResponse:
    # TODO: Replace with horizon-aware forecast generation for the target entity.
    return StubPredictionResponse(
        status="stub",
        request_type="forecast",
        todo="Implement time-series model loading and forecast generation.",
        payload={
            "entity_id": payload.entity_id,
            "horizon_days": payload.horizon_days,
            "forecast": [],
        },
    )


@router.post("/segmentation/predict", response_model=StubPredictionResponse)
def predict_segmentation(
    payload: SegmentationPredictionRequest,
) -> StubPredictionResponse:
    # TODO: Replace with actual clustering/segment assignment logic.
    return StubPredictionResponse(
        status="stub",
        request_type="segmentation",
        todo="Implement segment assignment using feature-layer inputs.",
        payload={
            "user_id": payload.user_id,
            "segment_scope": payload.segment_scope,
            "segment": None,
        },
    )

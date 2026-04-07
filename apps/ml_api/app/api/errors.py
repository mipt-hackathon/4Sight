import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.schemas.base import StubPredictionResponse
from app.domain.exceptions import (
    ArtifactNotFoundError,
    FeaturesNotFoundError,
    InvalidRequestDomainError,
    MlApiError,
    ModelLoadingError,
    ModelRuntimeError,
    NoActiveModelError,
    RegistryUnavailableError,
    UnsupportedScopeError,
)

logger = logging.getLogger(__name__)


def _error_response(request_type: str, status_code: int, error_code: str, message: str) -> JSONResponse:
    body = StubPredictionResponse(
        status="error",
        request_type=request_type,
        todo="",
        payload={"error_code": error_code, "error_message": message},
        trace_payload=None,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _use_case_from_path(request: Request) -> str:
    path = request.url.path
    for uc in ("churn", "recommendations", "forecast", "segmentation"):
        if uc in path:
            return uc
    return "unknown"


async def handle_features_not_found(request: Request, exc: FeaturesNotFoundError) -> JSONResponse:
    logger.warning("Features not found use_case=%s", exc.use_case)
    return _error_response(exc.use_case, 404, "FEATURES_NOT_FOUND", "No features found for the requested entity")


async def handle_no_active_model(request: Request, exc: NoActiveModelError) -> JSONResponse:
    logger.error("No active model use_case=%s model_name=%s", exc.use_case, exc.model_name)
    return _error_response(exc.use_case, 503, "NO_ACTIVE_MODEL", "No active model available for this use case")


async def handle_unsupported_scope(request: Request, exc: UnsupportedScopeError) -> JSONResponse:
    uc = _use_case_from_path(request)
    return _error_response(uc, 400, "UNSUPPORTED_SCOPE", f"Unsupported scope: {exc.scope}")


async def handle_invalid_request(request: Request, exc: InvalidRequestDomainError) -> JSONResponse:
    uc = _use_case_from_path(request)
    return _error_response(uc, 422, "INVALID_REQUEST", str(exc))


async def handle_registry_unavailable(request: Request, exc: RegistryUnavailableError) -> JSONResponse:
    uc = _use_case_from_path(request)
    return _error_response(uc, 503, "REGISTRY_UNAVAILABLE", "Model registry is unavailable")


async def handle_artifact_not_found(request: Request, exc: ArtifactNotFoundError) -> JSONResponse:
    uc = _use_case_from_path(request)
    return _error_response(uc, 503, "ARTIFACT_NOT_FOUND", "Model artifact not found")


async def handle_model_loading_error(request: Request, exc: ModelLoadingError) -> JSONResponse:
    uc = _use_case_from_path(request)
    return _error_response(uc, 503, "MODEL_LOADING_ERROR", "Model failed to load")


async def handle_model_runtime_error(request: Request, exc: ModelRuntimeError) -> JSONResponse:
    logger.error("Inference error use_case=%s", exc.use_case, exc_info=exc.cause)
    return _error_response(exc.use_case, 500, "INFERENCE_ERROR", "An error occurred during inference")


async def handle_ml_api_error(request: Request, exc: MlApiError) -> JSONResponse:
    uc = _use_case_from_path(request)
    logger.error("Unhandled MlApiError", exc_info=exc)
    return _error_response(uc, 500, "INTERNAL_ERROR", "An internal error occurred")


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    uc = _use_case_from_path(request)
    logger.error("Unexpected error", exc_info=exc)
    return _error_response(uc, 500, "INTERNAL_ERROR", "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(FeaturesNotFoundError, handle_features_not_found)
    app.add_exception_handler(NoActiveModelError, handle_no_active_model)
    app.add_exception_handler(UnsupportedScopeError, handle_unsupported_scope)
    app.add_exception_handler(InvalidRequestDomainError, handle_invalid_request)
    app.add_exception_handler(RegistryUnavailableError, handle_registry_unavailable)
    app.add_exception_handler(ArtifactNotFoundError, handle_artifact_not_found)
    app.add_exception_handler(ModelLoadingError, handle_model_loading_error)
    app.add_exception_handler(ModelRuntimeError, handle_model_runtime_error)
    app.add_exception_handler(MlApiError, handle_ml_api_error)
    app.add_exception_handler(Exception, handle_unexpected_error)

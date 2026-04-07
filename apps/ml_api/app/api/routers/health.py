import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.requests import Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ml/health")
def health() -> dict:
    return {"status": "ok", "service": "ml-api"}


@router.get("/ml/ready", response_model=None)
def ready(request: Request):
    runtime = request.app.state.runtime
    loaded = runtime.loaded_use_cases()
    if not loaded:
        return JSONResponse(status_code=503, content={"status": "not_ready", "loaded": []})
    return JSONResponse(status_code=200, content={"status": "ready", "loaded": loaded})

from fastapi import APIRouter

router = APIRouter()


@router.get("/ml/health")
def healthcheck() -> dict:
    # TODO: Keep this as a liveness endpoint.
    # TODO: Add separate readiness checks for model registry/artifacts later.
    return {
        "status": "ok",
        "service": "ml-api",
        "todo": (
            "Keep liveness lightweight; add a dedicated readiness check for model artifacts later."
        ),
    }

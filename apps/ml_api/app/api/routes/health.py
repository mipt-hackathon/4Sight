from fastapi import APIRouter

router = APIRouter()


@router.get("/ml/health")
def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "ml-api",
        "todo": "Add model registry, artifact, and dependency readiness checks.",
    }

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "backend",
        "todo": "Add dependency checks, version metadata, and readiness probes.",
    }

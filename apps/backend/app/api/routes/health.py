from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    # TODO: Keep this as a liveness endpoint.
    # TODO: Add separate readiness checks once dependencies are wired.
    return {
        "status": "ok",
        "service": "backend",
        "todo": (
            "Keep liveness lightweight; add a dedicated readiness check for postgres/redis later."
        ),
    }

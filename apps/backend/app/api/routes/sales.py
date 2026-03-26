from fastapi import APIRouter

router = APIRouter()


@router.get("/forecast")
def sales_forecast() -> dict:
    # TODO: Serve sales forecast data prepared by feature and serving jobs.
    return {
        "status": "stub",
        "forecast": [],
        "todo": "Implement sales forecast API contract and query logic.",
    }

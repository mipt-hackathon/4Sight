from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
def dashboard_overview() -> dict:
    # TODO: Read aggregate KPIs from mart/serving tables once those layers exist.
    return {
        "status": "stub",
        "view": "dashboard_overview",
        "sections": [
            "sales_summary",
            "customer_health",
            "campaign_performance",
            "logistics_snapshot",
        ],
        "todo": "Implement overview aggregation for BI-facing dashboard cards.",
    }

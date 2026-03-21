from fastapi import APIRouter

router = APIRouter()


@router.get("/{user_id}")
def get_customer_profile(user_id: str) -> dict:
    # TODO: Serve curated customer profile assembled from mart.customer_360.
    return {
        "status": "stub",
        "user_id": user_id,
        "profile": None,
        "todo": "Implement customer profile lookup from curated and serving tables.",
    }


@router.get("/{user_id}/churn")
def get_customer_churn(user_id: str) -> dict:
    # TODO: Proxy or fetch churn outputs from serving tables / ml-api integration.
    return {
        "status": "stub",
        "user_id": user_id,
        "churn": None,
        "todo": "Implement churn score retrieval and explanation payload.",
    }


@router.get("/{user_id}/recommendations")
def get_customer_recommendations(user_id: str) -> dict:
    # TODO: Return ranked products once recommendation serving is implemented.
    return {
        "status": "stub",
        "user_id": user_id,
        "recommendations": [],
        "todo": "Implement product recommendation retrieval for the MVP app.",
    }

from datetime import UTC, datetime

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from conftest import load_service_app


def _fake_retail_app_service():
    class FakeRetailAppService:
        def get_dashboard_overview(self) -> dict:
            return {
                "generated_at": datetime(2026, 4, 20, 12, 0, tzinfo=UTC).isoformat(),
                "sales_kpis": {
                    "total_revenue": 125000.0,
                    "total_orders": 420,
                    "total_customers": 180,
                    "avg_order_value": 297.62,
                    "last_sales_date": "2026-04-19",
                    "revenue_last_30d": 54200.0,
                    "orders_last_30d": 168,
                },
                "sales_trend": [
                    {"date": "2026-04-17", "value": 4100.0},
                    {"date": "2026-04-18", "value": 4380.0},
                    {"date": "2026-04-19", "value": 4520.0},
                ],
                "customer_health": {
                    "customers_total": 180,
                    "loyal_customers": 71,
                    "repeat_customer_rate": 0.46,
                    "active_customers_30d": 109,
                    "avg_ltv": 694.44,
                },
                "churn_monitor": {
                    "high_risk_customers": 24,
                    "medium_risk_customers": 61,
                    "high_risk_share": 0.1333,
                    "top_risk_segments": [
                        {
                            "segment": "at_risk",
                            "customers_count": 33,
                            "avg_revenue": 780.0,
                            "avg_orders": 3.4,
                            "avg_days_since_last_order": 58.0,
                            "high_risk_share": 0.48,
                        }
                    ],
                },
                "logistics_snapshot": {
                    "avg_ship_days": 1.8,
                    "avg_delivery_days": 4.2,
                    "delayed_delivery_rate": 0.14,
                    "returned_orders_rate": 0.08,
                },
                "category_watchlist": [
                    {
                        "category": "Shoes",
                        "order_items_count": 52,
                        "return_rate": 0.21,
                        "negative_review_rate": 0.12,
                        "dissatisfaction_score": 0.18,
                    }
                ],
                "segment_mix": [
                    {
                        "segment": "champions",
                        "customers_count": 44,
                        "avg_revenue": 1120.0,
                        "avg_orders": 5.4,
                        "avg_days_since_last_order": 9.0,
                        "high_risk_share": 0.03,
                    }
                ],
            }

        def search_customers(self, query: str | None, limit: int) -> dict:
            _ = (query, limit)
            return {
                "items": [
                    {
                        "user_id": 1,
                        "full_name": "Alice Example",
                        "email": "alice@example.com",
                        "city": "Moscow",
                        "country": "Russia",
                        "rfm_segment": "champions",
                        "churn_bucket": "low",
                        "total_revenue": 944.2,
                    }
                ]
            }

        def list_high_risk_customers(self, limit: int) -> dict:
            _ = limit
            return {
                "items": [
                    {
                        "user_id": 9,
                        "full_name": "Bob Risk",
                        "city": "Kazan",
                        "country": "Russia",
                        "rfm_segment": "at_risk",
                        "churn_probability": 0.81,
                        "churn_bucket": "high",
                        "total_revenue": 712.3,
                        "orders_count": 3,
                        "days_since_last_order": 67,
                        "top_factors": [
                            {
                                "feature": "days_since_last_order",
                                "label": "Давно не покупал",
                                "direction": "risk_up",
                            }
                        ],
                    }
                ]
            }

        def get_customer_profile(self, user_id: int) -> dict:
            return {
                "identity": {
                    "user_id": user_id,
                    "first_name": "Alice",
                    "last_name": "Example",
                    "email": "alice@example.com",
                    "gender": "F",
                    "age": 31,
                    "city": "Moscow",
                    "state": "Moscow",
                    "country": "Russia",
                    "traffic_source": "Search",
                    "is_loyal": True,
                },
                "commerce": {
                    "first_order_at": datetime(2024, 1, 10, 9, 0, tzinfo=UTC).isoformat(),
                    "last_order_at": datetime(2026, 4, 10, 9, 0, tzinfo=UTC).isoformat(),
                    "orders_count": 7,
                    "completed_orders_count": 5,
                    "shipped_orders_count": 1,
                    "cancelled_orders_count": 1,
                    "returned_orders_count": 1,
                    "order_items_count": 15,
                    "total_revenue": 944.2,
                    "avg_order_value": 134.89,
                    "days_since_last_order": 10,
                },
                "behavior": {
                    "first_event_at": datetime(2024, 1, 9, 12, 0, tzinfo=UTC).isoformat(),
                    "last_event_at": datetime(2026, 4, 18, 14, 0, tzinfo=UTC).isoformat(),
                    "event_count": 120,
                    "session_count": 22,
                    "home_events_count": 25,
                    "department_events_count": 18,
                    "product_events_count": 45,
                    "cart_events_count": 16,
                    "purchase_events_count": 9,
                    "cancel_events_count": 2,
                    "days_since_last_event": 2,
                },
                "segment": {
                    "rfm_score": "554",
                    "rfm_segment": "champions",
                    "recency_score": 5,
                    "frequency_score": 5,
                    "monetary_score": 4,
                    "predicted_segment": "loyal_high_value",
                },
                "favorite_categories": ["Shoes", "Outerwear"],
            }

        def get_customer_churn(self, user_id: int) -> dict:
            return {
                "user_id": user_id,
                "source": "heuristic_fallback",
                "churn_probability": 0.33,
                "churn_bucket": "medium",
                "top_factors": [
                    {
                        "feature": "days_since_last_order",
                        "label": "Давно не покупал",
                        "direction": "risk_up",
                    }
                ],
                "days_since_last_order": 10,
                "days_since_last_event": 2,
                "orders_count": 7,
                "total_revenue": 944.2,
                "rfm_segment": "champions",
            }

        def get_customer_recommendations(self, user_id: int, limit: int) -> dict:
            _ = limit
            return {
                "user_id": user_id,
                "source": "catalog_fallback",
                "churn_bucket": "medium",
                "excluded_categories": ["Accessories"],
                "items": [
                    {
                        "product_id": 101,
                        "product_name": "Trail Jacket",
                        "category": "Outerwear",
                        "brand": "North Ridge",
                        "price": 129.9,
                        "score": 0.88,
                        "reason": "Реактивация через любимую категорию",
                        "source": "catalog_fallback",
                    }
                ],
            }

        def get_retention_targets(self, limit: int, per_user: int) -> dict:
            _ = (limit, per_user)
            customer = self.list_high_risk_customers(limit=1)["items"][0]
            recommendations = self.get_customer_recommendations(
                user_id=customer["user_id"], limit=2
            )["items"]
            return {"items": [{"customer": customer, "recommendations": recommendations}]}

        def get_sales_forecast(self, entity_id: str, horizon_days: int) -> dict:
            return {
                "entity_id": entity_id,
                "summary": {
                    "source": "ml_api",
                    "horizon_days": horizon_days,
                    "last_actual_date": "2026-04-19",
                    "last_actual_value": 4520.0,
                    "avg_daily_forecast": 4705.0,
                    "forecast_total": 32935.0,
                },
                "history": [
                    {"date": "2026-04-17", "value": 4100.0},
                    {"date": "2026-04-18", "value": 4380.0},
                    {"date": "2026-04-19", "value": 4520.0},
                ],
                "forecast": [
                    {"date": "2026-04-20", "value": 4610.0},
                    {"date": "2026-04-21", "value": 4685.0},
                ],
            }

        def get_segments_summary(self) -> dict:
            return {
                "generated_at": datetime(2026, 4, 20, 12, 0, tzinfo=UTC).isoformat(),
                "items": [
                    {
                        "segment": "champions",
                        "customers_count": 44,
                        "avg_revenue": 1120.0,
                        "avg_orders": 5.4,
                        "avg_days_since_last_order": 9.0,
                        "high_risk_share": 0.03,
                    }
                ],
            }

    return FakeRetailAppService()


def _client() -> TestClient:
    app = load_service_app("backend")
    app.dependency_overrides[_find_dependency(app, "get_retail_app_service")] = (
        _fake_retail_app_service
    )
    return TestClient(app)


def _find_dependency(app, dependency_name: str):
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for dependency in route.dependant.dependencies:
            if getattr(dependency.call, "__name__", "") == dependency_name:
                return dependency.call
    raise AssertionError(f"Dependency {dependency_name} not found in app routes")


def test_dashboard_overview_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["sales_kpis"]["total_orders"] > 0
    assert isinstance(body["sales_trend"], list)
    assert isinstance(body["category_watchlist"], list)
    assert isinstance(body["segment_mix"], list)


def test_customer_search_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/customers/search", params={"q": "alice", "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert isinstance(body["items"], list)


def test_high_risk_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/customers/high-risk", params={"limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    if body["items"]:
        assert body["items"][0]["churn_probability"] >= 0.0


def test_customer_profile_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/customers/1")

    assert response.status_code == 200
    body = response.json()
    assert body["identity"]["user_id"] == 1
    assert "commerce" in body
    assert "behavior" in body
    assert "segment" in body


def test_customer_churn_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/customers/1/churn")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] in {"ml_api", "heuristic_fallback"}
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["churn_bucket"] in {"low", "medium", "high"}


def test_customer_recommendations_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/customers/1/recommendations", params={"limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["source"] in {"ml_api", "catalog_fallback"}
    assert isinstance(body["excluded_categories"], list)
    assert isinstance(body["items"], list)


def test_retention_targets_endpoint() -> None:
    with _client() as client:
        response = client.get(
            "/api/recommendations/retention-targets", params={"limit": 3, "per_user": 2}
        )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    if body["items"]:
        assert "customer" in body["items"][0]
        assert "recommendations" in body["items"][0]


def test_sales_forecast_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/sales/forecast", params={"horizon_days": 7})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["horizon_days"] == 7
    assert isinstance(body["history"], list)
    assert isinstance(body["forecast"], list)


def test_segments_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/segments")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    if body["items"]:
        assert "segment" in body["items"][0]
        assert "customers_count" in body["items"][0]


def test_superset_deep_dive_embed_endpoint() -> None:
    app = load_service_app("backend")

    class FakeSupersetEmbedService:
        def get_deep_dive_embed(self) -> dict[str, str]:
            return {
                "dashboard_slug": "retail-notebook-bi-deep-dive",
                "dashboard_title": "Retail Notebook BI Deep Dive",
                "dashboard_url": "http://localhost:18088/superset/dashboard/retail-notebook-bi-deep-dive/",
                "superset_domain": "http://localhost:18088",
                "embedded_id": "11111111-1111-1111-1111-111111111111",
                "guest_token": "guest-token",
            }

    app.dependency_overrides[_find_dependency(app, "get_superset_embed_service")] = (
        lambda: FakeSupersetEmbedService()
    )
    try:
        with TestClient(app) as client:
            response = client.get("/api/bi/deep-dive/embed")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["dashboard_slug"] == "retail-notebook-bi-deep-dive"
    assert body["superset_domain"] == "http://localhost:18088"
    assert body["guest_token"] == "guest-token"

from fastapi.testclient import TestClient

from conftest import load_service_app


def _client() -> TestClient:
    app = load_service_app("backend")
    return TestClient(app)


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

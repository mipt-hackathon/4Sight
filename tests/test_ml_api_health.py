from fastapi.testclient import TestClient

from conftest import load_service_app


def test_ml_api_health_endpoint() -> None:
    app = load_service_app("ml_api")
    client = TestClient(app)
    response = client.get("/ml/health")

    assert response.status_code == 200
    assert response.json()["service"] == "ml-api"

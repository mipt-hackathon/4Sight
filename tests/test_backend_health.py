from fastapi.testclient import TestClient

from conftest import load_service_app


def test_backend_health_endpoint() -> None:
    app = load_service_app("backend")
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["service"] == "backend"

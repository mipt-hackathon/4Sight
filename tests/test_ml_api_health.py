import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def test_ml_api_health_endpoint() -> None:
    root = Path(__file__).resolve().parents[1]
    ml_api_path = str(root / "apps" / "ml_api")

    preserved_app_modules = {
        name: module for name, module in sys.modules.items() if name.startswith("app")
    }

    sys.path.insert(0, ml_api_path)
    try:
        for module_name in list(sys.modules):
            if module_name.startswith("app"):
                sys.modules.pop(module_name)

        module = importlib.import_module("app.main")
        client = TestClient(module.app)
        response = client.get("/ml/health")

        assert response.status_code == 200
        assert response.json()["service"] == "ml-api"
    finally:
        sys.path.remove(ml_api_path)
        for module_name in list(sys.modules):
            if module_name.startswith("app"):
                sys.modules.pop(module_name)
        sys.modules.update(preserved_app_modules)

import importlib
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]

for relative_path in [
    "libs/common/src",
    "jobs",
]:
    resolved = str(ROOT / relative_path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def load_service_app(service_name: str) -> FastAPI:
    service_path = str(ROOT / "apps" / service_name)
    preserved_app_modules = {
        name: module for name, module in sys.modules.items() if name.startswith("app")
    }

    sys.path.insert(0, service_path)
    try:
        for module_name in list(sys.modules):
            if module_name.startswith("app"):
                sys.modules.pop(module_name)

        module = importlib.import_module("app.main")
        return module.app
    finally:
        sys.path.remove(service_path)
        for module_name in list(sys.modules):
            if module_name.startswith("app"):
                sys.modules.pop(module_name)
        sys.modules.update(preserved_app_modules)

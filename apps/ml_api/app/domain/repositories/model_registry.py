from typing import Protocol

from app.domain.dto.registry import ModelVersionInfo


class ModelRegistryRepository(Protocol):
    def get_active_model_version(self, model_name: str) -> ModelVersionInfo | None: ...

    def list_model_versions(self, model_name: str) -> list[ModelVersionInfo]: ...

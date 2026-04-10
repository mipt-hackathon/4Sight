from typing import Any, Protocol

from app.api.schemas.base import ModelRoutingOptions


class RuntimeManager(Protocol):
    def predict_churn(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_recommendations(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_forecast(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_segmentation(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def loaded_use_cases(self) -> list[str]: ...


class ModelNameResolver(Protocol):
    def resolve(self, use_case: str, model_key: str | None = None) -> str: ...

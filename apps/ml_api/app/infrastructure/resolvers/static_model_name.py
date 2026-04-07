class StaticModelNameResolver:
    _MAP = {
        "churn": "churn_model",
        "recommendations": "recsys_model",
        "forecast": "forecast_model",
        "segmentation": "segmentation_model",
    }

    def resolve(self, use_case: str, model_key: str | None = None) -> str:
        if use_case not in self._MAP:
            raise ValueError(f"Unknown use case: {use_case}")
        return self._MAP[use_case]

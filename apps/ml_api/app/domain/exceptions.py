class MlApiError(Exception):
    """Base class for all ml_api domain exceptions."""


# Application errors (4xx)

class FeaturesNotFoundError(MlApiError):
    def __init__(self, use_case: str, key: str) -> None:
        self.use_case = use_case
        self.key = key
        super().__init__(f"No features found for use_case={use_case} key={key}")


class NoActiveModelError(MlApiError):
    def __init__(self, use_case: str, model_name: str) -> None:
        self.use_case = use_case
        self.model_name = model_name
        super().__init__(f"No active model for use_case={use_case} model_name={model_name}")


class UnsupportedScopeError(MlApiError):
    def __init__(self, scope: str) -> None:
        self.scope = scope
        super().__init__(f"Unsupported scope: {scope}")


class InvalidRequestDomainError(MlApiError):
    pass


# Infrastructure / runtime errors (5xx)

class RegistryUnavailableError(MlApiError):
    pass


class ArtifactNotFoundError(MlApiError):
    def __init__(self, model_name: str, path: str) -> None:
        self.model_name = model_name
        self.path = path
        super().__init__(f"Artifact not found for model_name={model_name} path={path}")


class ModelLoadingError(MlApiError):
    def __init__(self, model_name: str, cause: Exception) -> None:
        self.model_name = model_name
        self.cause = cause
        super().__init__(f"Failed to load model_name={model_name}: {cause}")


class ModelRuntimeError(MlApiError):
    def __init__(self, use_case: str, cause: Exception) -> None:
        self.use_case = use_case
        self.cause = cause
        super().__init__(f"Inference error for use_case={use_case}: {cause}")

from functools import lru_cache

from common.config.settings import AppSettings
from pydantic import Field


class BackendSettings(AppSettings):
    ml_api_base_url: str = Field(
        default="http://ml-api:8001",
        validation_alias="ML_API_BASE_URL",
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:13000,http://127.0.0.1:13000",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    ml_api_timeout_seconds: float = Field(
        default=5.0,
        validation_alias="ML_API_TIMEOUT_SECONDS",
    )


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    return BackendSettings()

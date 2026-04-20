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
    superset_internal_url: str = Field(
        default="http://superset:8088",
        validation_alias="SUPERSET_INTERNAL_URL",
    )
    superset_public_url: str = Field(
        default="http://localhost:18088",
        validation_alias="SUPERSET_PUBLIC_URL",
    )
    superset_admin_username: str = Field(
        default="admin",
        validation_alias="SUPERSET_ADMIN_USERNAME",
    )
    superset_admin_password: str = Field(
        default="admin",
        validation_alias="SUPERSET_ADMIN_PASSWORD",
    )
    superset_api_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="SUPERSET_API_TIMEOUT_SECONDS",
    )
    superset_embed_allowed_domains: str = Field(
        default="http://localhost:13000,http://127.0.0.1:13000",
        validation_alias="SUPERSET_EMBED_ALLOWED_DOMAINS",
    )
    superset_embed_dashboard_slug: str = Field(
        default="retail-notebook-bi-deep-dive",
        validation_alias="SUPERSET_EMBED_DASHBOARD_SLUG",
    )
    superset_embed_dashboard_title: str = Field(
        default="Retail Notebook BI Deep Dive",
        validation_alias="SUPERSET_EMBED_DASHBOARD_TITLE",
    )
    superset_guest_username: str = Field(
        default="retail_frontend_guest",
        validation_alias="SUPERSET_GUEST_USERNAME",
    )


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    return BackendSettings()

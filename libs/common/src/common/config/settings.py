from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Minimal shared settings used across services and jobs."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="retail-analytics-service", validation_alias="APP_NAME")
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    app_log_level: str = Field(default="INFO", validation_alias="APP_LOG_LEVEL")
    postgres_dsn: str = Field(
        default="postgresql+psycopg://retail:retail@localhost:5432/retail_analytics",
        validation_alias="POSTGRES_DSN",
    )
    alembic_database_url: str = Field(
        default="postgresql+psycopg://retail:retail@localhost:5432/retail_analytics",
        validation_alias="ALEMBIC_DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    data_raw_path: Path = Field(default=Path("/workspace/data/raw"))
    model_artifacts_path: Path = Field(default=Path("/workspace/artifacts/models"))


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

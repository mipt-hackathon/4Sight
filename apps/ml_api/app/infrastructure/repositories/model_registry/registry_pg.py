import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import ProgrammingError

from app.domain.dto.registry import ModelVersionInfo

logger = logging.getLogger(__name__)

_QUERY = text(
    """
    SELECT DISTINCT ON (model_name)
        model_name, model_version, stage, artifact_path, is_active, created_at
    FROM serving.model_registry
    WHERE model_name = :model_name
      AND is_active = TRUE
    ORDER BY model_name, model_version DESC, created_at DESC
    """
)

_LIST_QUERY = text(
    """
    SELECT model_name, model_version, stage, artifact_path, is_active, created_at
    FROM serving.model_registry
    WHERE model_name = :model_name
    ORDER BY model_version DESC, created_at DESC
    """
)


class ModelRegistryRepositoryImpl:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_active_model_version(self, model_name: str) -> ModelVersionInfo | None:
        try:
            with self._engine.connect() as conn:
                return self._get_active(conn, model_name)
        except ProgrammingError:
            logger.warning("serving.model_registry table not found or inaccessible")
            return None

    def _get_active(self, conn: Connection, model_name: str) -> ModelVersionInfo | None:
        row = conn.execute(_QUERY, {"model_name": model_name}).mappings().one_or_none()
        if row is None:
            return None
        return ModelVersionInfo(**dict(row))

    def list_model_versions(self, model_name: str) -> list[ModelVersionInfo]:
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(_LIST_QUERY, {"model_name": model_name}).mappings().all()
                return [ModelVersionInfo(**dict(r)) for r in rows]
        except ProgrammingError:
            logger.warning("serving.model_registry table not found or inaccessible")
            return []

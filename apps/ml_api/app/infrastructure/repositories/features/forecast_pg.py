import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app.domain.dto.features import ForecastHistory

logger = logging.getLogger(__name__)

_PRIMARY_QUERY = text(
    "SELECT * FROM feature.forecast WHERE entity_id = :eid ORDER BY date DESC LIMIT :lim"
)

_FALLBACK_QUERY = text(
    """
    SELECT date, revenue AS value
    FROM mart.sales_daily
    WHERE entity_id = :eid OR :eid = 'all'
    ORDER BY date DESC
    LIMIT :lim
    """
)

_DEFAULT_HISTORY_WINDOW = 90


class ForecastFeatureRepositoryImpl:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_timeseries_for_entity(
        self, entity_id: str, history_window: int | None = None
    ) -> ForecastHistory | None:
        lim = history_window or _DEFAULT_HISTORY_WINDOW
        with self._engine.connect() as conn:
            rows: list[dict[str, Any]] | None = None
            try:
                result = conn.execute(_PRIMARY_QUERY, {"eid": entity_id, "lim": lim}).mappings().all()
                if result:
                    logger.debug("feature_source=feature.forecast entity_id=%s", entity_id)
                    rows = [dict(r) for r in result]
            except ProgrammingError:
                pass

            if rows is None:
                result = conn.execute(_FALLBACK_QUERY, {"eid": entity_id, "lim": lim}).mappings().all()
                if not result:
                    return None
                logger.debug("feature_source=mart_fallback entity_id=%s", entity_id)
                rows = [dict(r) for r in result]

        return ForecastHistory(entity_id=entity_id, time_series=rows)

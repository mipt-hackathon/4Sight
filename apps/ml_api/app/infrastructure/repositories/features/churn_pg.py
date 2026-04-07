import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app.domain.dto.features import ChurnFeatures

logger = logging.getLogger(__name__)

_PRIMARY_QUERY = text("SELECT * FROM feature.churn WHERE user_id = :uid LIMIT 1")

_FALLBACK_QUERY = text(
    """
    SELECT c.user_id, c.orders_count, c.total_revenue, c.days_since_last_order,
           r.recency_score, r.frequency_score, r.monetary_score, r.rfm_score, r.rfm_segment,
           b.event_count, b.session_count, b.days_since_last_event
    FROM mart.customer_360 c
    LEFT JOIN mart.rfm r USING (user_id)
    LEFT JOIN mart.behavior_metrics b USING (user_id)
    WHERE c.user_id = :uid
    LIMIT 1
    """
)


class ChurnFeatureRepositoryImpl:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_features_for_user(self, user_id: str, as_of_date: date | None = None) -> ChurnFeatures | None:
        if as_of_date is not None:
            logger.debug("feature_source=churn as_of_date=%s user_id=%s", as_of_date, user_id)

        with self._engine.connect() as conn:
            try:
                row = conn.execute(_PRIMARY_QUERY, {"uid": user_id}).mappings().one_or_none()
                if row is not None:
                    logger.debug("feature_source=feature.churn user_id=%s", user_id)
                    return ChurnFeatures(**dict(row))
            except ProgrammingError:
                pass  # feature.churn table not yet populated

            row = conn.execute(_FALLBACK_QUERY, {"uid": user_id}).mappings().one_or_none()
            if row is None:
                return None
            logger.debug("feature_source=mart_fallback user_id=%s", user_id)
            return ChurnFeatures(**dict(row))

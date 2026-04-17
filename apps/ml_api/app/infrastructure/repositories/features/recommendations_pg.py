import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app.domain.dto.features import RecommendationsUserFeatures

logger = logging.getLogger(__name__)

_PRIMARY_QUERY = text("SELECT * FROM feature.recsys WHERE user_id = :uid LIMIT 1")

_FALLBACK_QUERY = text(
    """
    SELECT c.user_id, c.orders_count, c.total_revenue, c.days_since_last_order,
           r.recency_score, r.frequency_score, r.monetary_score
    FROM mart.customer_360 c
    LEFT JOIN mart.rfm r USING (user_id)
    WHERE c.user_id = :uid
    LIMIT 1
    """
)


class RecommendationsFeatureRepositoryImpl:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_user_features(self, user_id: str) -> RecommendationsUserFeatures | None:
        with self._engine.connect() as conn:
            try:
                row = conn.execute(_PRIMARY_QUERY, {"uid": user_id}).mappings().one_or_none()
                if row is not None:
                    logger.debug("feature_source=feature.recsys user_id=%s", user_id)
                    return RecommendationsUserFeatures(**dict(row))
            except ProgrammingError:
                conn.rollback()

            row = conn.execute(_FALLBACK_QUERY, {"uid": user_id}).mappings().one_or_none()
            if row is None:
                return None
            logger.debug("feature_source=mart_fallback user_id=%s", user_id)
            return RecommendationsUserFeatures(**dict(row))

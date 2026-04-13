from collections.abc import Sequence
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError

_NEGATIVE_REVIEW_PATTERN = (
    "(disappointed|poor experience|terrible|awful|returning it|not what i expected|low quality)"
)

_RISK_SCORE_SQL = """
LEAST(
    0.95,
    (
        CASE
            WHEN c.days_since_last_order IS NULL THEN 0.35
            WHEN c.days_since_last_order >= 120 THEN 0.35
            WHEN c.days_since_last_order >= 60 THEN 0.22
            WHEN c.days_since_last_order >= 30 THEN 0.12
            ELSE 0.03
        END
        + CASE
            WHEN c.days_since_last_event IS NULL THEN 0.20
            WHEN c.days_since_last_event >= 45 THEN 0.20
            WHEN c.days_since_last_event >= 21 THEN 0.12
            WHEN c.days_since_last_event >= 7 THEN 0.05
            ELSE 0.01
        END
        + CASE
            WHEN COALESCE(c.orders_count, 0) > 0
                 AND COALESCE(c.returned_orders_count::NUMERIC / NULLIF(c.orders_count, 0), 0) >= 0.30 THEN 0.14
            WHEN COALESCE(c.orders_count, 0) > 0
                 AND COALESCE(c.returned_orders_count::NUMERIC / NULLIF(c.orders_count, 0), 0) >= 0.15 THEN 0.08
            ELSE 0.00
        END
        + CASE
            WHEN COALESCE(c.orders_count, 0) > 0
                 AND COALESCE(c.cancelled_orders_count::NUMERIC / NULLIF(c.orders_count, 0), 0) >= 0.30 THEN 0.12
            WHEN COALESCE(c.orders_count, 0) > 0
                 AND COALESCE(c.cancelled_orders_count::NUMERIC / NULLIF(c.orders_count, 0), 0) >= 0.15 THEN 0.06
            ELSE 0.00
        END
        + CASE
            WHEN COALESCE(r.rfm_segment, 'unclassified') = 'hibernating' THEN 0.20
            WHEN COALESCE(r.rfm_segment, 'unclassified') = 'at_risk' THEN 0.16
            WHEN COALESCE(r.rfm_segment, 'unclassified') = 'potential_loyalist' THEN 0.08
            ELSE 0.00
        END
        + CASE
            WHEN COALESCE(c.total_revenue, 0) >= 500 AND COALESCE(c.orders_count, 0) <= 2 THEN 0.05
            ELSE 0.00
        END
    )::NUMERIC
)
"""

_RISK_CTE = f"""
WITH customer_risk AS (
    SELECT
        c.user_id,
        c.first_name,
        c.last_name,
        c.email,
        c.city,
        c.country,
        c.total_revenue,
        c.orders_count,
        c.days_since_last_order,
        c.days_since_last_event,
        c.returned_orders_count,
        c.cancelled_orders_count,
        c.avg_order_value,
        COALESCE(r.rfm_segment, 'unclassified') AS rfm_segment,
        ROUND({_RISK_SCORE_SQL}, 4) AS churn_probability
    FROM mart.customer_360 AS c
    LEFT JOIN mart.rfm AS r
        USING (user_id)
)
"""

_CUSTOMER_PROFILE_QUERY = text(
    """
    SELECT
        c.user_id,
        c.first_name,
        c.last_name,
        c.email,
        c.gender,
        c.age,
        c.city,
        c.state,
        c.country,
        c.traffic_source,
        c.is_loyal,
        c.first_order_at,
        c.last_order_at,
        c.orders_count,
        c.completed_orders_count,
        c.shipped_orders_count,
        c.cancelled_orders_count,
        c.returned_orders_count,
        c.order_items_count,
        c.total_revenue,
        c.avg_order_value,
        c.days_since_last_order,
        c.first_event_at,
        c.last_event_at,
        c.event_count,
        c.session_count,
        c.home_events_count,
        c.department_events_count,
        c.product_events_count,
        c.cart_events_count,
        c.purchase_events_count,
        c.cancel_events_count,
        c.days_since_last_event,
        r.rfm_score,
        r.rfm_segment,
        r.recency_score,
        r.frequency_score,
        r.monetary_score
    FROM mart.customer_360 AS c
    LEFT JOIN mart.rfm AS r
        USING (user_id)
    WHERE c.user_id = :user_id
    LIMIT 1
    """
)

_TOP_CATEGORIES_QUERY = text(
    """
    SELECT category
    FROM clean.order_items
    WHERE user_id = :user_id
      AND category IS NOT NULL
    GROUP BY category
    ORDER BY COUNT(*) DESC, category ASC
    LIMIT :limit
    """
)

_CUSTOMER_SEARCH_QUERY = text(
    _RISK_CTE
    + """
    SELECT
        user_id,
        TRIM(CONCAT_WS(' ', first_name, last_name)) AS full_name,
        email,
        city,
        country,
        rfm_segment,
        CASE
            WHEN churn_probability >= 0.70 THEN 'high'
            WHEN churn_probability >= 0.40 THEN 'medium'
            ELSE 'low'
        END AS churn_bucket,
        COALESCE(total_revenue, 0)::FLOAT AS total_revenue
    FROM customer_risk
    WHERE (
        :apply_filter = FALSE
        OR CAST(user_id AS TEXT) ILIKE :pattern
        OR CONCAT_WS(' ', first_name, last_name) ILIKE :pattern
        OR COALESCE(email, '') ILIKE :pattern
    )
    ORDER BY total_revenue DESC, user_id ASC
    LIMIT :limit
    """
)

_HIGH_RISK_QUERY = text(
    _RISK_CTE
    + """
    SELECT
        user_id,
        TRIM(CONCAT_WS(' ', first_name, last_name)) AS full_name,
        city,
        country,
        rfm_segment,
        churn_probability::FLOAT AS churn_probability,
        CASE
            WHEN churn_probability >= 0.70 THEN 'high'
            WHEN churn_probability >= 0.40 THEN 'medium'
            ELSE 'low'
        END AS churn_bucket,
        COALESCE(total_revenue, 0)::FLOAT AS total_revenue,
        COALESCE(orders_count, 0) AS orders_count,
        days_since_last_order,
        days_since_last_event,
        returned_orders_count,
        cancelled_orders_count
    FROM customer_risk
    WHERE churn_probability >= :min_probability
    ORDER BY churn_probability DESC, total_revenue DESC, user_id ASC
    LIMIT :limit
    """
)

_HIGH_RISK_SUMMARY_QUERY = text(
    _RISK_CTE
    + """
    SELECT
        COUNT(*) FILTER (WHERE churn_probability >= 0.70) AS high_risk_customers,
        COUNT(*) FILTER (WHERE churn_probability >= 0.40 AND churn_probability < 0.70) AS medium_risk_customers,
        ROUND(AVG(CASE WHEN churn_probability >= 0.70 THEN 1 ELSE 0 END)::NUMERIC, 4)::FLOAT AS high_risk_share
    FROM customer_risk
    """
)

_SEGMENT_SUMMARY_QUERY = text(
    _RISK_CTE
    + """
    SELECT
        rfm_segment AS segment,
        COUNT(*) AS customers_count,
        ROUND(AVG(COALESCE(total_revenue, 0))::NUMERIC, 2)::FLOAT AS avg_revenue,
        ROUND(AVG(COALESCE(orders_count, 0))::NUMERIC, 2)::FLOAT AS avg_orders,
        ROUND(AVG(days_since_last_order)::NUMERIC, 2)::FLOAT AS avg_days_since_last_order,
        ROUND(AVG(CASE WHEN churn_probability >= 0.70 THEN 1 ELSE 0 END)::NUMERIC, 4)::FLOAT AS high_risk_share
    FROM customer_risk
    GROUP BY rfm_segment
    ORDER BY customers_count DESC, segment ASC
    """
)

_SALES_KPI_QUERY = text(
    """
    SELECT
        COALESCE(SUM(gross_revenue), 0)::FLOAT AS total_revenue,
        COALESCE(SUM(orders_count), 0) AS total_orders,
        (SELECT COUNT(*) FROM mart.customer_360) AS total_customers,
        MAX(sales_date) AS last_sales_date,
        COALESCE(SUM(gross_revenue) FILTER (
            WHERE sales_date >= CURRENT_DATE - INTERVAL '30 days'
        ), 0)::FLOAT AS revenue_last_30d,
        COALESCE(SUM(orders_count) FILTER (
            WHERE sales_date >= CURRENT_DATE - INTERVAL '30 days'
        ), 0) AS orders_last_30d
    FROM mart.sales_daily
    """
)

_SALES_TREND_QUERY = text(
    """
    SELECT sales_date AS date, gross_revenue::FLOAT AS value
    FROM mart.sales_daily
    ORDER BY sales_date DESC
    LIMIT :limit
    """
)

_CUSTOMER_HEALTH_QUERY = text(
    """
    SELECT
        COUNT(*) AS customers_total,
        COUNT(*) FILTER (WHERE is_loyal IS TRUE) AS loyal_customers,
        ROUND(AVG(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END)::NUMERIC, 4)::FLOAT AS repeat_customer_rate,
        COUNT(*) FILTER (WHERE COALESCE(days_since_last_order, 999999) <= 30) AS active_customers_30d,
        ROUND(AVG(COALESCE(total_revenue, 0))::NUMERIC, 2)::FLOAT AS avg_ltv
    FROM mart.customer_360
    """
)

_LOGISTICS_QUERY = text(
    """
    SELECT
        ROUND(AVG(EXTRACT(EPOCH FROM (shipped_at - created_at)) / 86400.0)::NUMERIC, 2)::FLOAT AS avg_ship_days,
        ROUND(AVG(EXTRACT(EPOCH FROM (delivered_at - created_at)) / 86400.0)::NUMERIC, 2)::FLOAT AS avg_delivery_days,
        ROUND(AVG(CASE
            WHEN delivered_at IS NOT NULL
             AND EXTRACT(EPOCH FROM (delivered_at - created_at)) / 86400.0 > 5 THEN 1
            ELSE 0
        END)::NUMERIC, 4)::FLOAT AS delayed_delivery_rate,
        ROUND(AVG(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END)::NUMERIC, 4)::FLOAT AS returned_orders_rate
    FROM clean.orders
    """
)

_CATEGORY_WATCHLIST_QUERY = text(
    f"""
    WITH category_quality AS (
        SELECT
            oi.category,
            COUNT(*) AS order_items_count,
            AVG(CASE WHEN o.status = 'Returned' THEN 1 ELSE 0 END) AS return_rate,
            AVG(CASE
                WHEN LOWER(COALESCE(oi.customer_review, '')) ~ '{_NEGATIVE_REVIEW_PATTERN}' THEN 1
                ELSE 0
            END) AS negative_review_rate
        FROM clean.order_items AS oi
        JOIN clean.orders AS o
            USING (order_id)
        WHERE oi.category IS NOT NULL
        GROUP BY oi.category
    )
    SELECT
        category,
        order_items_count,
        ROUND(return_rate::NUMERIC, 4)::FLOAT AS return_rate,
        ROUND(negative_review_rate::NUMERIC, 4)::FLOAT AS negative_review_rate,
        ROUND((return_rate * 0.6 + negative_review_rate * 0.4)::NUMERIC, 4)::FLOAT AS dissatisfaction_score
    FROM category_quality
    WHERE order_items_count >= 50
    ORDER BY dissatisfaction_score DESC, order_items_count DESC, category ASC
    LIMIT :limit
    """
)

_SALES_HISTORY_QUERY = text(
    """
    SELECT sales_date AS date, gross_revenue::FLOAT AS value
    FROM mart.sales_daily
    WHERE (:entity_id = 'all')
    ORDER BY sales_date DESC
    LIMIT :limit
    """
)

_RECOMMENDATION_CANDIDATES_QUERY = text(
    f"""
    WITH category_quality AS (
        SELECT
            oi.category,
            COUNT(*) AS order_items_count,
            AVG(CASE WHEN o.status = 'Returned' THEN 1 ELSE 0 END) AS return_rate,
            AVG(CASE
                WHEN LOWER(COALESCE(oi.customer_review, '')) ~ '{_NEGATIVE_REVIEW_PATTERN}' THEN 1
                ELSE 0
            END) AS negative_review_rate
        FROM clean.order_items AS oi
        JOIN clean.orders AS o
            USING (order_id)
        WHERE oi.category IS NOT NULL
        GROUP BY oi.category
    ),
    bad_categories AS (
        SELECT category
        FROM category_quality
        WHERE order_items_count >= 50
          AND (return_rate * 0.6 + negative_review_rate * 0.4) >= 0.18
    ),
    user_pref AS (
        SELECT category
        FROM clean.order_items
        WHERE user_id = :user_id
          AND category IS NOT NULL
        GROUP BY category
        ORDER BY COUNT(*) DESC, category ASC
        LIMIT 3
    ),
    candidate_pool AS (
        SELECT
            oi.product_id,
            MAX(oi.product_name) AS product_name,
            MAX(oi.category) AS category,
            MAX(oi.brand) AS brand,
            ROUND(AVG(oi.sale_price)::NUMERIC, 2)::FLOAT AS price,
            COUNT(*) AS popularity
        FROM clean.order_items AS oi
        JOIN clean.orders AS o
            USING (order_id)
        WHERE oi.product_name IS NOT NULL
          AND oi.category IS NOT NULL
          AND oi.product_id NOT IN (
              SELECT DISTINCT product_id
              FROM clean.order_items
              WHERE user_id = :user_id
          )
          AND oi.category NOT IN (SELECT category FROM bad_categories)
          AND (
              :prefer_known_categories = FALSE
              OR NOT EXISTS (SELECT 1 FROM user_pref)
              OR oi.category IN (SELECT category FROM user_pref)
          )
        GROUP BY oi.product_id
    )
    SELECT
        product_id,
        product_name,
        category,
        brand,
        price,
        popularity
    FROM candidate_pool
    ORDER BY popularity DESC, price DESC, product_id ASC
    LIMIT :limit
    """
)

_PRODUCT_DETAILS_QUERY = text(
    """
    SELECT
        product_id,
        MAX(product_name) AS product_name,
        MAX(category) AS category,
        MAX(brand) AS brand,
        ROUND(AVG(sale_price)::NUMERIC, 2)::FLOAT AS price
    FROM clean.order_items
    WHERE product_id IN :product_ids
    GROUP BY product_id
    """
).bindparams(bindparam("product_ids", expanding=True))


class AnalyticsDataUnavailableError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "Аналитические таблицы еще не подготовлены. После `docker compose up -d --build` "
            "нужно отдельно прогнать `docker compose run --rm etl` и "
            "`docker compose run --rm marts-builder`."
        )


class AnalyticsRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def fetch_customer_profile(self, user_id: int) -> dict[str, Any] | None:
        return self._execute_one_or_none(_CUSTOMER_PROFILE_QUERY, {"user_id": user_id})

    def fetch_top_categories(self, user_id: int, limit: int = 5) -> list[str]:
        rows = self._execute_all(
            _TOP_CATEGORIES_QUERY,
            {"user_id": user_id, "limit": limit},
        )
        return [str(row["category"]) for row in rows]

    def search_customers(self, query: str | None, limit: int) -> list[dict[str, Any]]:
        query_text = query.strip() if query else None
        pattern = f"%{query_text}%" if query_text else "%"
        return self._execute_all(
            _CUSTOMER_SEARCH_QUERY,
            {
                "apply_filter": query_text is not None,
                "pattern": pattern,
                "limit": limit,
            },
        )

    def fetch_high_risk_customers(
        self,
        limit: int,
        min_probability: float = 0.55,
    ) -> list[dict[str, Any]]:
        return self._execute_all(
            _HIGH_RISK_QUERY,
            {"limit": limit, "min_probability": min_probability},
        )

    def fetch_high_risk_summary(self) -> dict[str, Any]:
        return self._execute_one(_HIGH_RISK_SUMMARY_QUERY)

    def fetch_segment_summary(self) -> list[dict[str, Any]]:
        return self._execute_all(_SEGMENT_SUMMARY_QUERY)

    def fetch_sales_kpis(self) -> dict[str, Any]:
        return self._execute_one(_SALES_KPI_QUERY)

    def fetch_sales_trend(self, limit: int = 30) -> list[dict[str, Any]]:
        return self._execute_all(_SALES_TREND_QUERY, {"limit": limit})

    def fetch_customer_health(self) -> dict[str, Any]:
        return self._execute_one(_CUSTOMER_HEALTH_QUERY)

    def fetch_logistics_snapshot(self) -> dict[str, Any]:
        return self._execute_one(_LOGISTICS_QUERY)

    def fetch_category_watchlist(self, limit: int = 5) -> list[dict[str, Any]]:
        return self._execute_all(_CATEGORY_WATCHLIST_QUERY, {"limit": limit})

    def fetch_sales_history(self, entity_id: str, limit: int = 90) -> list[dict[str, Any]]:
        return self._execute_all(
            _SALES_HISTORY_QUERY,
            {"entity_id": entity_id, "limit": limit},
        )

    def fetch_recommendation_candidates(
        self,
        user_id: int,
        limit: int,
        prefer_known_categories: bool,
    ) -> list[dict[str, Any]]:
        return self._execute_all(
            _RECOMMENDATION_CANDIDATES_QUERY,
            {
                "user_id": user_id,
                "limit": limit,
                "prefer_known_categories": prefer_known_categories,
            },
        )

    def fetch_product_details(self, product_ids: Sequence[int]) -> list[dict[str, Any]]:
        if not product_ids:
            return []
        return self._execute_all(
            _PRODUCT_DETAILS_QUERY,
            {"product_ids": list(product_ids)},
        )

    def _execute_one(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            with self._engine.connect() as connection:
                row = connection.execute(statement, params or {}).mappings().one()
        except DBAPIError as exc:
            self._raise_if_data_unavailable(exc)
            raise
        return dict(row)

    def _execute_one_or_none(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            with self._engine.connect() as connection:
                row = connection.execute(statement, params or {}).mappings().one_or_none()
        except DBAPIError as exc:
            self._raise_if_data_unavailable(exc)
            raise
        return dict(row) if row is not None else None

    def _execute_all(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            with self._engine.connect() as connection:
                rows = connection.execute(statement, params or {}).mappings().all()
        except DBAPIError as exc:
            self._raise_if_data_unavailable(exc)
            raise
        return [dict(row) for row in rows]

    def _raise_if_data_unavailable(self, exc: DBAPIError) -> None:
        message = str(getattr(exc, "orig", exc)).lower()
        if (
            "does not exist" in message
            or "undefinedtable" in message
            or "invalid schema" in message
            or "undefined schema" in message
        ):
            raise AnalyticsDataUnavailableError() from exc

import logging
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from typing import Any

from fastapi import HTTPException

from app.api.models import (
    CategoryWatchlistItem,
    ChurnMonitorSnapshot,
    CustomerChurnResponse,
    CustomerHealthSnapshot,
    CustomerLookupItem,
    CustomerProfileBehavior,
    CustomerProfileCommerce,
    CustomerProfileIdentity,
    CustomerProfileResponse,
    CustomerProfileSegment,
    CustomerRecommendationsResponse,
    CustomerSearchResponse,
    DashboardKpi,
    DashboardOverviewResponse,
    ForecastSummary,
    HighRiskCustomerItem,
    HighRiskCustomersResponse,
    LogisticsSnapshot,
    RecommendationItem,
    RetentionTargetItem,
    RetentionTargetsResponse,
    RiskFactor,
    SalesForecastResponse,
    SegmentBreakdownItem,
    SegmentsResponse,
    TrendPoint,
)
from app.integrations.ml_api_client import MlApiClient, MlApiClientError
from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class RetailAppService:
    def __init__(self, repository: AnalyticsRepository, ml_api_client: MlApiClient) -> None:
        self._repository = repository
        self._ml_api_client = ml_api_client

    def get_dashboard_overview(self) -> DashboardOverviewResponse:
        sales_kpis_row = self._repository.fetch_sales_kpis()
        sales_trend_rows = self._repository.fetch_sales_trend(limit=30)
        customer_health_row = self._repository.fetch_customer_health()
        churn_summary_row = self._repository.fetch_high_risk_summary()
        logistics_row = self._repository.fetch_logistics_snapshot()
        watchlist_rows = self._repository.fetch_category_watchlist(limit=5)
        segment_rows = self._repository.fetch_segment_summary()

        total_orders = int(sales_kpis_row["total_orders"] or 0)
        total_revenue = self._to_float(sales_kpis_row["total_revenue"])
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0.0

        sales_kpis = DashboardKpi(
            total_revenue=total_revenue,
            total_orders=total_orders,
            total_customers=int(sales_kpis_row["total_customers"] or 0),
            avg_order_value=avg_order_value,
            last_sales_date=sales_kpis_row.get("last_sales_date"),
            revenue_last_30d=self._to_float(sales_kpis_row["revenue_last_30d"]),
            orders_last_30d=int(sales_kpis_row["orders_last_30d"] or 0),
        )

        sales_trend = [
            TrendPoint(date=row["date"], value=self._to_float(row["value"]))
            for row in reversed(sales_trend_rows)
        ]

        customer_health = CustomerHealthSnapshot(
            customers_total=int(customer_health_row["customers_total"] or 0),
            loyal_customers=int(customer_health_row["loyal_customers"] or 0),
            repeat_customer_rate=self._to_float(customer_health_row["repeat_customer_rate"]),
            active_customers_30d=int(customer_health_row["active_customers_30d"] or 0),
            avg_ltv=self._to_float(customer_health_row["avg_ltv"]),
        )

        segment_mix = [self._segment_item_from_row(row) for row in segment_rows]
        top_risk_segments = sorted(
            segment_mix,
            key=lambda item: (item.high_risk_share or 0.0, item.customers_count),
            reverse=True,
        )[:3]
        churn_monitor = ChurnMonitorSnapshot(
            high_risk_customers=int(churn_summary_row["high_risk_customers"] or 0),
            medium_risk_customers=int(churn_summary_row["medium_risk_customers"] or 0),
            high_risk_share=self._to_float(churn_summary_row["high_risk_share"]),
            top_risk_segments=top_risk_segments,
        )

        logistics_snapshot = LogisticsSnapshot(
            avg_ship_days=self._optional_float(logistics_row.get("avg_ship_days")),
            avg_delivery_days=self._optional_float(logistics_row.get("avg_delivery_days")),
            delayed_delivery_rate=self._to_float(logistics_row["delayed_delivery_rate"]),
            returned_orders_rate=self._to_float(logistics_row["returned_orders_rate"]),
        )

        category_watchlist = [
            CategoryWatchlistItem(**self._normalize_watchlist_row(row)) for row in watchlist_rows
        ]

        return DashboardOverviewResponse(
            generated_at=datetime.now(UTC),
            sales_kpis=sales_kpis,
            sales_trend=sales_trend,
            customer_health=customer_health,
            churn_monitor=churn_monitor,
            logistics_snapshot=logistics_snapshot,
            category_watchlist=category_watchlist,
            segment_mix=segment_mix,
        )

    def search_customers(self, query: str | None, limit: int) -> CustomerSearchResponse:
        rows = self._repository.search_customers(query=query, limit=limit)
        return CustomerSearchResponse(
            items=[
                CustomerLookupItem(
                    user_id=int(row["user_id"]),
                    full_name=row["full_name"] or f"User {row['user_id']}",
                    email=row.get("email"),
                    city=row.get("city"),
                    country=row.get("country"),
                    rfm_segment=row.get("rfm_segment"),
                    churn_bucket=row.get("churn_bucket"),
                    total_revenue=self._to_float(row["total_revenue"]),
                )
                for row in rows
            ]
        )

    def list_high_risk_customers(self, limit: int) -> HighRiskCustomersResponse:
        rows = self._repository.fetch_high_risk_customers(limit=limit)
        return HighRiskCustomersResponse(items=[self._high_risk_item_from_row(row) for row in rows])

    def get_customer_profile(self, user_id: int) -> CustomerProfileResponse:
        row = self._repository.fetch_customer_profile(user_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Customer {user_id} not found")

        predicted_segment = None
        try:
            segmentation_payload = self._ml_api_client.predict_segmentation(user_id)
            predicted_segment = segmentation_payload.get("segment")
        except MlApiClientError as exc:
            logger.info("Segmentation fallback for user_id=%s due_to=%s", user_id, exc.error_code)

        identity = CustomerProfileIdentity(
            user_id=int(row["user_id"]),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            gender=row.get("gender"),
            age=row.get("age"),
            city=row.get("city"),
            state=row.get("state"),
            country=row.get("country"),
            traffic_source=row.get("traffic_source"),
            is_loyal=row.get("is_loyal"),
        )
        commerce = CustomerProfileCommerce(
            first_order_at=row.get("first_order_at"),
            last_order_at=row.get("last_order_at"),
            orders_count=int(row["orders_count"] or 0),
            completed_orders_count=int(row["completed_orders_count"] or 0),
            shipped_orders_count=int(row["shipped_orders_count"] or 0),
            cancelled_orders_count=int(row["cancelled_orders_count"] or 0),
            returned_orders_count=int(row["returned_orders_count"] or 0),
            order_items_count=int(row["order_items_count"] or 0),
            total_revenue=self._to_float(row["total_revenue"]),
            avg_order_value=self._to_float(row["avg_order_value"]),
            days_since_last_order=self._optional_int(row.get("days_since_last_order")),
        )
        behavior = CustomerProfileBehavior(
            first_event_at=row.get("first_event_at"),
            last_event_at=row.get("last_event_at"),
            event_count=int(row["event_count"] or 0),
            session_count=int(row["session_count"] or 0),
            home_events_count=int(row["home_events_count"] or 0),
            department_events_count=int(row["department_events_count"] or 0),
            product_events_count=int(row["product_events_count"] or 0),
            cart_events_count=int(row["cart_events_count"] or 0),
            purchase_events_count=int(row["purchase_events_count"] or 0),
            cancel_events_count=int(row["cancel_events_count"] or 0),
            days_since_last_event=self._optional_int(row.get("days_since_last_event")),
        )
        segment = CustomerProfileSegment(
            rfm_score=row.get("rfm_score"),
            rfm_segment=row.get("rfm_segment"),
            recency_score=self._optional_int(row.get("recency_score")),
            frequency_score=self._optional_int(row.get("frequency_score")),
            monetary_score=self._optional_int(row.get("monetary_score")),
            predicted_segment=predicted_segment,
        )

        return CustomerProfileResponse(
            identity=identity,
            commerce=commerce,
            behavior=behavior,
            segment=segment,
            favorite_categories=self._repository.fetch_top_categories(user_id, limit=5),
        )

    def get_customer_churn(self, user_id: int) -> CustomerChurnResponse:
        row = self._repository.fetch_customer_profile(user_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Customer {user_id} not found")

        try:
            payload = self._ml_api_client.predict_churn(user_id)
            factors = [
                self._factor_from_ml_payload(item) for item in payload.get("top_factors") or []
            ]
            return CustomerChurnResponse(
                user_id=user_id,
                source="ml_api",
                churn_probability=self._to_float(payload.get("churn_probability")),
                churn_bucket=str(payload.get("churn_bucket") or "unknown"),
                top_factors=factors,
                days_since_last_order=self._optional_int(row.get("days_since_last_order")),
                days_since_last_event=self._optional_int(row.get("days_since_last_event")),
                orders_count=int(row["orders_count"] or 0),
                total_revenue=self._to_float(row["total_revenue"]),
                rfm_segment=row.get("rfm_segment"),
            )
        except MlApiClientError as exc:
            logger.info("Churn fallback for user_id=%s due_to=%s", user_id, exc.error_code)
            fallback = self._heuristic_churn_from_row(row)
            return CustomerChurnResponse(
                user_id=user_id,
                source="heuristic_fallback",
                churn_probability=fallback["probability"],
                churn_bucket=fallback["bucket"],
                top_factors=fallback["top_factors"],
                days_since_last_order=self._optional_int(row.get("days_since_last_order")),
                days_since_last_event=self._optional_int(row.get("days_since_last_event")),
                orders_count=int(row["orders_count"] or 0),
                total_revenue=self._to_float(row["total_revenue"]),
                rfm_segment=row.get("rfm_segment"),
            )

    def get_customer_recommendations(
        self, user_id: int, limit: int
    ) -> CustomerRecommendationsResponse:
        row = self._repository.fetch_customer_profile(user_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Customer {user_id} not found")

        churn = self.get_customer_churn(user_id)
        excluded_categories = self._excluded_categories(limit=5)
        items, source, _ = self._build_recommendations(
            user_id=user_id,
            limit=limit,
            churn_bucket=churn.churn_bucket,
            excluded_categories=excluded_categories,
        )
        return CustomerRecommendationsResponse(
            user_id=user_id,
            source=source,
            churn_bucket=churn.churn_bucket,
            excluded_categories=excluded_categories,
            items=items,
        )

    def get_retention_targets(self, limit: int, per_user: int) -> RetentionTargetsResponse:
        high_risk_items = self.list_high_risk_customers(limit=limit).items
        excluded_categories = self._excluded_categories(limit=5)
        ml_api_available = True
        items: list[RetentionTargetItem] = []
        for customer in high_risk_items:
            recs, _, ml_api_available = self._build_recommendations(
                user_id=customer.user_id,
                churn_bucket=customer.churn_bucket,
                limit=per_user,
                excluded_categories=excluded_categories,
                use_ml_api=ml_api_available,
            )
            items.append(RetentionTargetItem(customer=customer, recommendations=recs))
        return RetentionTargetsResponse(items=items)

    def get_sales_forecast(self, entity_id: str, horizon_days: int) -> SalesForecastResponse:
        history_rows = self._repository.fetch_sales_history(entity_id=entity_id, limit=90)
        if not history_rows:
            raise HTTPException(
                status_code=404, detail=f"No sales history found for entity '{entity_id}'"
            )

        history_points = [
            TrendPoint(date=row["date"], value=self._to_float(row["value"]))
            for row in reversed(history_rows)
        ]

        try:
            payload = self._ml_api_client.predict_forecast(
                entity_id=entity_id, horizon_days=horizon_days
            )
            forecast_points = [
                TrendPoint(date=self._parse_date(item["date"]), value=self._to_float(item["value"]))
                for item in payload.get("forecast") or []
            ]
            source = "ml_api"
        except MlApiClientError as exc:
            logger.info("Forecast fallback for entity_id=%s due_to=%s", entity_id, exc.error_code)
            forecast_points = self._heuristic_forecast(history_points, horizon_days)
            source = "trend_fallback"

        last_actual = history_points[-1] if history_points else None
        forecast_values = [point.value for point in forecast_points]
        summary = ForecastSummary(
            source=source,
            horizon_days=horizon_days,
            last_actual_date=last_actual.date if last_actual else None,
            last_actual_value=last_actual.value if last_actual else None,
            avg_daily_forecast=round(mean(forecast_values), 2) if forecast_values else 0.0,
            forecast_total=round(sum(forecast_values), 2),
        )
        return SalesForecastResponse(
            entity_id=entity_id,
            summary=summary,
            history=history_points,
            forecast=forecast_points,
        )

    def get_segments_summary(self) -> SegmentsResponse:
        segment_rows = self._repository.fetch_segment_summary()
        return SegmentsResponse(
            generated_at=datetime.now(UTC),
            items=[self._segment_item_from_row(row) for row in segment_rows],
        )

    def get_category_watchlist(self, limit: int) -> list[CategoryWatchlistItem]:
        rows = self._repository.fetch_category_watchlist(limit=limit)
        return [CategoryWatchlistItem(**self._normalize_watchlist_row(row)) for row in rows]

    def _excluded_categories(self, limit: int) -> list[str]:
        return [item.category for item in self.get_category_watchlist(limit=limit)]

    def _build_recommendations(
        self,
        *,
        user_id: int,
        churn_bucket: str | None,
        limit: int,
        excluded_categories: list[str],
        use_ml_api: bool = True,
    ) -> tuple[list[RecommendationItem], str, bool]:
        ml_api_available = use_ml_api

        if use_ml_api:
            try:
                payload = self._ml_api_client.predict_recommendations(user_id, limit)
                raw_items = payload.get("items") or []
                product_ids: list[int] = []
                for item in raw_items:
                    item_id = item.get("item_id")
                    if isinstance(item_id, str) and item_id.isdigit():
                        product_ids.append(int(item_id))
                    elif isinstance(item_id, int):
                        product_ids.append(item_id)
                detailed = self._repository.fetch_product_details(product_ids)
                detailed_by_id = {int(row["product_id"]): row for row in detailed}
                enriched_items: list[RecommendationItem] = []
                for item in raw_items:
                    item_id = item.get("item_id")
                    if isinstance(item_id, str) and item_id.isdigit():
                        product_id = int(item_id)
                    elif isinstance(item_id, int):
                        product_id = item_id
                    else:
                        continue
                    detail = detailed_by_id.get(product_id)
                    if detail is None:
                        continue
                    if detail.get("category") in excluded_categories:
                        continue
                    enriched_items.append(
                        RecommendationItem(
                            product_id=product_id,
                            product_name=str(detail["product_name"]),
                            category=detail.get("category"),
                            brand=detail.get("brand"),
                            price=self._to_float(detail["price"]),
                            score=self._optional_float(item.get("score")),
                            reason=str(item.get("reason") or "ml_ranked_item"),
                            source="ml_api",
                        )
                    )
                if enriched_items:
                    return enriched_items[:limit], "ml_api", ml_api_available
                logger.info(
                    "ML recommendations for user_id=%s were not mappable to product catalog; using fallback",  # noqa: E501
                    user_id,
                )
            except MlApiClientError as exc:
                logger.info(
                    "Recommendations fallback for user_id=%s due_to=%s", user_id, exc.error_code
                )
                if exc.status_code == 503 or exc.error_code in {
                    "NO_ACTIVE_MODEL",
                    "UPSTREAM_UNAVAILABLE",
                }:
                    ml_api_available = False

        fallback_items = self._fallback_recommendations(
            user_id=user_id,
            churn_bucket=churn_bucket,
            limit=limit,
        )
        return fallback_items, "catalog_fallback", ml_api_available

    def _fallback_recommendations(
        self,
        user_id: int,
        churn_bucket: str | None,
        limit: int,
    ) -> list[RecommendationItem]:
        prefer_known_categories = churn_bucket == "high"
        rows = self._repository.fetch_recommendation_candidates(
            user_id=user_id,
            limit=limit,
            prefer_known_categories=prefer_known_categories,
        )
        reason = (
            "retention_pick_from_familiar_category"
            if prefer_known_categories
            else "popular_safe_product"
        )
        return [
            RecommendationItem(
                product_id=int(row["product_id"]),
                product_name=str(row["product_name"]),
                category=row.get("category"),
                brand=row.get("brand"),
                price=self._to_float(row["price"]),
                score=self._optional_float(row.get("popularity")),
                reason=reason,
                source="catalog_fallback",
            )
            for row in rows
        ]

    def _high_risk_item_from_row(self, row: dict[str, Any]) -> HighRiskCustomerItem:
        fallback = self._heuristic_churn_from_row(row)
        return HighRiskCustomerItem(
            user_id=int(row["user_id"]),
            full_name=row.get("full_name") or f"User {row['user_id']}",
            city=row.get("city"),
            country=row.get("country"),
            rfm_segment=row.get("rfm_segment"),
            churn_probability=self._to_float(row["churn_probability"]),
            churn_bucket=str(row.get("churn_bucket") or fallback["bucket"]),
            total_revenue=self._to_float(row["total_revenue"]),
            orders_count=int(row["orders_count"] or 0),
            days_since_last_order=self._optional_int(row.get("days_since_last_order")),
            top_factors=fallback["top_factors"],
        )

    def _segment_item_from_row(self, row: dict[str, Any]) -> SegmentBreakdownItem:
        return SegmentBreakdownItem(
            segment=str(row.get("segment") or "unclassified"),
            customers_count=int(row["customers_count"] or 0),
            avg_revenue=self._to_float(row["avg_revenue"]),
            avg_orders=self._to_float(row["avg_orders"]),
            avg_days_since_last_order=self._optional_float(row.get("avg_days_since_last_order")),
            high_risk_share=self._optional_float(row.get("high_risk_share")),
        )

    def _heuristic_churn_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        probability = 0.0
        factors: list[tuple[float, RiskFactor]] = []

        days_since_last_order = self._optional_int(row.get("days_since_last_order"))
        if days_since_last_order is None or days_since_last_order >= 120:
            probability += 0.35
            factors.append(
                (0.35, RiskFactor(feature="days_since_last_order", label="Давно не было заказа"))
            )
        elif days_since_last_order >= 60:
            probability += 0.22
            factors.append(
                (
                    0.22,
                    RiskFactor(feature="days_since_last_order", label="Снижение частоты заказов"),
                )
            )
        elif days_since_last_order >= 30:
            probability += 0.12
            factors.append(
                (0.12, RiskFactor(feature="days_since_last_order", label="Есть пауза в покупках"))
            )
        else:
            probability += 0.03

        days_since_last_event = self._optional_int(row.get("days_since_last_event"))
        if days_since_last_event is None or days_since_last_event >= 45:
            probability += 0.20
            factors.append(
                (
                    0.20,
                    RiskFactor(
                        feature="days_since_last_event",
                        label="Пользователь давно не проявлял активность",
                    ),
                )
            )
        elif days_since_last_event >= 21:
            probability += 0.12
            factors.append(
                (
                    0.12,
                    RiskFactor(
                        feature="days_since_last_event", label="Снизилась поведенческая активность"
                    ),
                )
            )
        elif days_since_last_event >= 7:
            probability += 0.05

        orders_count = int(row.get("orders_count") or 0)
        returned_orders_count = int(row.get("returned_orders_count") or 0)
        cancelled_orders_count = int(row.get("cancelled_orders_count") or 0)
        if orders_count > 0:
            return_rate = returned_orders_count / orders_count
            cancel_rate = cancelled_orders_count / orders_count
        else:
            return_rate = 0.0
            cancel_rate = 0.0

        if return_rate >= 0.30:
            probability += 0.14
            factors.append((0.14, RiskFactor(feature="returns", label="Высокая доля возвратов")))
        elif return_rate >= 0.15:
            probability += 0.08
            factors.append(
                (0.08, RiskFactor(feature="returns", label="Есть заметная доля возвратов"))
            )

        if cancel_rate >= 0.30:
            probability += 0.12
            factors.append(
                (0.12, RiskFactor(feature="cancellations", label="Высокая доля отмен заказов"))
            )
        elif cancel_rate >= 0.15:
            probability += 0.06
            factors.append(
                (0.06, RiskFactor(feature="cancellations", label="Есть повышенная доля отмен"))
            )

        rfm_segment = str(row.get("rfm_segment") or "unclassified")
        if rfm_segment == "hibernating":
            probability += 0.20
            factors.append((0.20, RiskFactor(feature="rfm_segment", label="Сегмент hibernating")))
        elif rfm_segment == "at_risk":
            probability += 0.16
            factors.append((0.16, RiskFactor(feature="rfm_segment", label="Сегмент at_risk")))
        elif rfm_segment == "potential_loyalist":
            probability += 0.08
            factors.append(
                (0.08, RiskFactor(feature="rfm_segment", label="Сегмент potential_loyalist"))
            )

        if self._to_float(row.get("total_revenue")) >= 500 and orders_count <= 2:
            probability += 0.05
            factors.append(
                (
                    0.05,
                    RiskFactor(feature="ltv_gap", label="Высокий LTV при низкой текущей частоте"),
                )
            )

        probability = round(min(probability, 0.95), 4)
        if probability >= 0.70:
            bucket = "high"
        elif probability >= 0.40:
            bucket = "medium"
        else:
            bucket = "low"

        top_factors = [
            factor for _, factor in sorted(factors, key=lambda item: item[0], reverse=True)[:3]
        ]
        return {
            "probability": probability,
            "bucket": bucket,
            "top_factors": top_factors,
        }

    def _heuristic_forecast(self, history: list[TrendPoint], horizon_days: int) -> list[TrendPoint]:
        if not history:
            return []
        last_28 = history[-28:] if len(history) >= 28 else history
        last_14 = history[-14:] if len(history) >= 14 else history
        prev_14 = history[-28:-14] if len(history) >= 28 else history[:-14]

        recent_avg = mean(point.value for point in last_14)
        prior_avg = mean(point.value for point in prev_14) if prev_14 else recent_avg
        if prior_avg == 0:
            growth = 0.0
        else:
            growth = max(min((recent_avg - prior_avg) / prior_avg, 0.20), -0.20)

        weekday_bases: dict[int, float] = {}
        for weekday in range(7):
            weekday_values = [point.value for point in last_28 if point.date.weekday() == weekday]
            weekday_bases[weekday] = mean(weekday_values) if weekday_values else recent_avg

        last_date = history[-1].date
        forecast: list[TrendPoint] = []
        for offset in range(1, horizon_days + 1):
            current_date = last_date + timedelta(days=offset)
            seasonal_base = weekday_bases[current_date.weekday()]
            growth_multiplier = 1 + (growth * min(offset / 14, 1.0))
            forecast.append(
                TrendPoint(
                    date=current_date,
                    value=round(seasonal_base * growth_multiplier, 2),
                )
            )
        return forecast

    @staticmethod
    def _factor_from_ml_payload(item: dict[str, Any]) -> RiskFactor:
        feature = str(item.get("feature") or "unknown")
        label_map = {
            "days_since_last_order": "Давно не было заказа",
            "days_since_last_event": "Снизилась активность в приложении",
            "rfm_segment": "Рискованный RFM-сегмент",
        }
        return RiskFactor(
            feature=feature,
            label=label_map.get(feature, feature),
            direction=str(item.get("direction") or "risk_up"),
        )

    @staticmethod
    def _parse_date(value: Any) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @staticmethod
    def _normalize_watchlist_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "category": str(row["category"]),
            "order_items_count": int(row["order_items_count"] or 0),
            "return_rate": float(row["return_rate"] or 0.0),
            "negative_review_rate": float(row["negative_review_rate"] or 0.0),
            "dissatisfaction_score": float(row["dissatisfaction_score"] or 0.0),
        }

    @staticmethod
    def _to_float(value: Any) -> float:
        return round(float(value or 0.0), 4)

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value), 4)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None
        return int(value)

from datetime import date, datetime

from pydantic import BaseModel, Field


class CustomerLookupItem(BaseModel):
    user_id: int
    full_name: str
    email: str | None = None
    city: str | None = None
    country: str | None = None
    rfm_segment: str | None = None
    churn_bucket: str | None = None
    total_revenue: float


class CustomerSearchResponse(BaseModel):
    items: list[CustomerLookupItem]


class RiskFactor(BaseModel):
    feature: str
    label: str
    direction: str = "risk_up"


class HighRiskCustomerItem(BaseModel):
    user_id: int
    full_name: str
    city: str | None = None
    country: str | None = None
    rfm_segment: str | None = None
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    churn_bucket: str
    total_revenue: float
    orders_count: int
    days_since_last_order: int | None = None
    top_factors: list[RiskFactor]


class HighRiskCustomersResponse(BaseModel):
    items: list[HighRiskCustomerItem]


class DashboardKpi(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    avg_order_value: float
    last_sales_date: date | None = None
    revenue_last_30d: float
    orders_last_30d: int


class TrendPoint(BaseModel):
    date: date
    value: float


class CustomerHealthSnapshot(BaseModel):
    customers_total: int
    loyal_customers: int
    repeat_customer_rate: float
    active_customers_30d: int
    avg_ltv: float


class SegmentBreakdownItem(BaseModel):
    segment: str
    customers_count: int
    avg_revenue: float
    avg_orders: float
    avg_days_since_last_order: float | None = None
    high_risk_share: float | None = None


class ChurnMonitorSnapshot(BaseModel):
    high_risk_customers: int
    medium_risk_customers: int
    high_risk_share: float
    top_risk_segments: list[SegmentBreakdownItem]


class LogisticsSnapshot(BaseModel):
    avg_ship_days: float | None = None
    avg_delivery_days: float | None = None
    delayed_delivery_rate: float
    returned_orders_rate: float


class CategoryWatchlistItem(BaseModel):
    category: str
    order_items_count: int
    return_rate: float
    negative_review_rate: float
    dissatisfaction_score: float


class DashboardOverviewResponse(BaseModel):
    generated_at: datetime
    sales_kpis: DashboardKpi
    sales_trend: list[TrendPoint]
    customer_health: CustomerHealthSnapshot
    churn_monitor: ChurnMonitorSnapshot
    logistics_snapshot: LogisticsSnapshot
    category_watchlist: list[CategoryWatchlistItem]
    segment_mix: list[SegmentBreakdownItem]


class CustomerProfileIdentity(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    gender: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    traffic_source: str | None = None
    is_loyal: bool | None = None


class CustomerProfileCommerce(BaseModel):
    first_order_at: datetime | None = None
    last_order_at: datetime | None = None
    orders_count: int
    completed_orders_count: int
    shipped_orders_count: int
    cancelled_orders_count: int
    returned_orders_count: int
    order_items_count: int
    total_revenue: float
    avg_order_value: float
    days_since_last_order: int | None = None


class CustomerProfileBehavior(BaseModel):
    first_event_at: datetime | None = None
    last_event_at: datetime | None = None
    event_count: int
    session_count: int
    home_events_count: int
    department_events_count: int
    product_events_count: int
    cart_events_count: int
    purchase_events_count: int
    cancel_events_count: int
    days_since_last_event: int | None = None


class CustomerProfileSegment(BaseModel):
    rfm_score: str | None = None
    rfm_segment: str | None = None
    recency_score: int | None = None
    frequency_score: int | None = None
    monetary_score: int | None = None
    predicted_segment: str | None = None


class CustomerProfileResponse(BaseModel):
    identity: CustomerProfileIdentity
    commerce: CustomerProfileCommerce
    behavior: CustomerProfileBehavior
    segment: CustomerProfileSegment
    favorite_categories: list[str]


class CustomerChurnResponse(BaseModel):
    user_id: int
    source: str
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    churn_bucket: str
    top_factors: list[RiskFactor]
    days_since_last_order: int | None = None
    days_since_last_event: int | None = None
    orders_count: int
    total_revenue: float
    rfm_segment: str | None = None


class RecommendationItem(BaseModel):
    product_id: int
    product_name: str
    category: str | None = None
    brand: str | None = None
    price: float
    score: float | None = None
    reason: str
    source: str


class CustomerRecommendationsResponse(BaseModel):
    user_id: int
    source: str
    churn_bucket: str | None = None
    excluded_categories: list[str]
    items: list[RecommendationItem]


class RetentionTargetItem(BaseModel):
    customer: HighRiskCustomerItem
    recommendations: list[RecommendationItem]


class RetentionTargetsResponse(BaseModel):
    items: list[RetentionTargetItem]


class ForecastSummary(BaseModel):
    source: str
    horizon_days: int
    last_actual_date: date | None = None
    last_actual_value: float | None = None
    avg_daily_forecast: float
    forecast_total: float


class SalesForecastResponse(BaseModel):
    entity_id: str
    summary: ForecastSummary
    history: list[TrendPoint]
    forecast: list[TrendPoint]


class SegmentsResponse(BaseModel):
    generated_at: datetime
    items: list[SegmentBreakdownItem]


class SupersetDeepDiveEmbedResponse(BaseModel):
    dashboard_slug: str
    dashboard_title: str
    dashboard_url: str
    superset_domain: str
    embedded_id: str
    guest_token: str

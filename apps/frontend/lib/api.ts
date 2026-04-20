import { env } from "./env";

export class ApiRequestError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

export function isDataNotReadyError(error: unknown): error is ApiRequestError {
  return error instanceof ApiRequestError && error.status === 503;
}

export type HealthResponse = {
  status: string;
  service: string;
};

export type TrendPoint = {
  date: string;
  value: number;
};

export type SegmentBreakdownItem = {
  segment: string;
  customers_count: number;
  avg_revenue: number;
  avg_orders: number;
  avg_days_since_last_order: number | null;
  high_risk_share: number | null;
};

export type DashboardOverviewResponse = {
  generated_at: string;
  sales_kpis: {
    total_revenue: number;
    total_orders: number;
    total_customers: number;
    avg_order_value: number;
    last_sales_date: string | null;
    revenue_last_30d: number;
    orders_last_30d: number;
  };
  sales_trend: TrendPoint[];
  customer_health: {
    customers_total: number;
    loyal_customers: number;
    repeat_customer_rate: number;
    active_customers_30d: number;
    avg_ltv: number;
  };
  churn_monitor: {
    high_risk_customers: number;
    medium_risk_customers: number;
    high_risk_share: number;
    top_risk_segments: SegmentBreakdownItem[];
  };
  logistics_snapshot: {
    avg_ship_days: number | null;
    avg_delivery_days: number | null;
    delayed_delivery_rate: number;
    returned_orders_rate: number;
  };
  category_watchlist: {
    category: string;
    order_items_count: number;
    return_rate: number;
    negative_review_rate: number;
    dissatisfaction_score: number;
  }[];
  segment_mix: SegmentBreakdownItem[];
};

export type HighRiskCustomerItem = {
  user_id: number;
  full_name: string;
  city: string | null;
  country: string | null;
  rfm_segment: string | null;
  churn_probability: number;
  churn_bucket: string;
  total_revenue: number;
  orders_count: number;
  days_since_last_order: number | null;
  top_factors: {
    feature: string;
    label: string;
    direction: string;
  }[];
};

export type HighRiskCustomersResponse = {
  items: HighRiskCustomerItem[];
};

export type CustomerSearchResponse = {
  items: {
    user_id: number;
    full_name: string;
    email: string | null;
    city: string | null;
    country: string | null;
    rfm_segment: string | null;
    churn_bucket: string | null;
    total_revenue: number;
  }[];
};

export type CustomerProfileResponse = {
  identity: {
    user_id: number;
    first_name: string | null;
    last_name: string | null;
    email: string | null;
    gender: string | null;
    age: number | null;
    city: string | null;
    state: string | null;
    country: string | null;
    traffic_source: string | null;
    is_loyal: boolean | null;
  };
  commerce: {
    first_order_at: string | null;
    last_order_at: string | null;
    orders_count: number;
    completed_orders_count: number;
    shipped_orders_count: number;
    cancelled_orders_count: number;
    returned_orders_count: number;
    order_items_count: number;
    total_revenue: number;
    avg_order_value: number;
    days_since_last_order: number | null;
  };
  behavior: {
    first_event_at: string | null;
    last_event_at: string | null;
    event_count: number;
    session_count: number;
    home_events_count: number;
    department_events_count: number;
    product_events_count: number;
    cart_events_count: number;
    purchase_events_count: number;
    cancel_events_count: number;
    days_since_last_event: number | null;
  };
  segment: {
    rfm_score: string | null;
    rfm_segment: string | null;
    recency_score: number | null;
    frequency_score: number | null;
    monetary_score: number | null;
    predicted_segment: string | null;
  };
  favorite_categories: string[];
};

export type CustomerChurnResponse = {
  user_id: number;
  source: string;
  churn_probability: number;
  churn_bucket: string;
  top_factors: {
    feature: string;
    label: string;
    direction: string;
  }[];
  days_since_last_order: number | null;
  days_since_last_event: number | null;
  orders_count: number;
  total_revenue: number;
  rfm_segment: string | null;
};

export type CustomerRecommendationsResponse = {
  user_id: number;
  source: string;
  churn_bucket: string | null;
  excluded_categories: string[];
  items: {
    product_id: number;
    product_name: string;
    category: string | null;
    brand: string | null;
    price: number;
    score: number | null;
    reason: string;
    source: string;
  }[];
};

export type RetentionTargetsResponse = {
  items: {
    customer: HighRiskCustomerItem;
    recommendations: CustomerRecommendationsResponse["items"];
  }[];
};

export type SalesForecastResponse = {
  entity_id: string;
  summary: {
    source: string;
    horizon_days: number;
    last_actual_date: string | null;
    last_actual_value: number | null;
    avg_daily_forecast: number;
    forecast_total: number;
  };
  history: TrendPoint[];
  forecast: TrendPoint[];
};

export type SegmentsResponse = {
  generated_at: string;
  items: SegmentBreakdownItem[];
};

export type SupersetDeepDiveEmbedResponse = {
  dashboard_slug: string;
  dashboard_title: string;
  dashboard_url: string;
  superset_domain: string;
  embedded_id: string;
  guest_token: string;
};

function resolveBackendBaseUrl(): string {
  return typeof window === "undefined"
    ? env.backendInternalUrl
    : env.backendUrl;
}

async function readErrorDetail(
  response: Response,
): Promise<string | undefined> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined;
  }

  try {
    const payload = (await response.json()) as {
      detail?: string;
      error_code?: string;
      payload?: { error_message?: string };
    };
    return payload.detail ?? payload.payload?.error_message;
  } catch {
    return undefined;
  }
}

async function fetchJson<T>(
  path: string,
  searchParams?: Record<string, string | number | undefined>,
): Promise<T> {
  const url = new URL(path, resolveBackendBaseUrl());
  for (const [key, value] of Object.entries(searchParams ?? {})) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url.toString(), {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiRequestError(
      `Request failed: ${response.status} ${response.statusText}`,
      response.status,
      detail,
    );
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getBackendHealth() {
    return fetchJson<HealthResponse>("/api/health");
  },
  getMlHealth() {
    return fetchJson<HealthResponse>(`${env.mlApiUrl}/ml/health`);
  },
  getDashboardOverview() {
    return fetchJson<DashboardOverviewResponse>("/api/dashboard/overview");
  },
  searchCustomers(query?: string, limit = 10) {
    return fetchJson<CustomerSearchResponse>("/api/customers/search", {
      q: query,
      limit,
    });
  },
  getHighRiskCustomers(limit = 20) {
    return fetchJson<HighRiskCustomersResponse>("/api/customers/high-risk", {
      limit,
    });
  },
  getCustomerProfile(userId: number) {
    return fetchJson<CustomerProfileResponse>(`/api/customers/${userId}`);
  },
  getCustomerChurn(userId: number) {
    return fetchJson<CustomerChurnResponse>(`/api/customers/${userId}/churn`);
  },
  getCustomerRecommendations(userId: number, limit = 5) {
    return fetchJson<CustomerRecommendationsResponse>(
      `/api/customers/${userId}/recommendations`,
      { limit },
    );
  },
  getRetentionTargets(limit = 8, perUser = 3) {
    return fetchJson<RetentionTargetsResponse>(
      "/api/recommendations/retention-targets",
      {
        limit,
        per_user: perUser,
      },
    );
  },
  getSalesForecast(horizonDays = 30, entityId = "all") {
    return fetchJson<SalesForecastResponse>("/api/sales/forecast", {
      horizon_days: horizonDays,
      entity_id: entityId,
    });
  },
  getSegments() {
    return fetchJson<SegmentsResponse>("/api/segments");
  },
  getSupersetDeepDiveEmbed() {
    return fetchJson<SupersetDeepDiveEmbedResponse>("/api/bi/deep-dive/embed");
  },
};

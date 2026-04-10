# `apps/ml_api` - Final Serving Architecture

**Project:** 4Sight - Retail Analytics ML Platform

**Document:** Final architecture - single source of truth for `apps/ml_api` implementation

**Session:** C (synthesis of Session A draft + Session B review + developer decisions Q1–Q6)

**Status:** Final

---

## Table of Contents

1. [Boundaries and Responsibilities](#1-boundaries-and-responsibilities)
2. [Use Cases and API Contract](#2-use-cases-and-api-contract)
3. [Architectural Style and Layers](#3-architectural-style-and-layers)
4. [Feature Data and Feature Repositories](#4-feature-data-and-feature-repositories)
5. [Shared Utils and Common Components](#5-shared-utils-and-common-components)
6. [Model Registry and Model Versioning](#6-model-registry-and-model-versioning)
7. [Logging](#7-logging)
8. [Metrics, Tracing, Observability](#8-metrics-tracing-observability)
9. [Pydantic Schemas](#9-pydantic-schemas)
10. [Package and File Structure](#10-package-and-file-structure)
11. [Runtime Manager and Model Loading](#11-runtime-manager-and-model-loading)
12. [SQL Contracts and Repository Interfaces](#12-sql-contracts-and-repository-interfaces)
13. [Error Handling and HTTP Mapping](#13-error-handling-and-http-mapping)
14. [Health and Ready Endpoints](#14-health-and-ready-endpoints)
15. [Testing Strategy](#15-testing-strategy)
16. [Implementation Plan](#16-implementation-plan)
17. [MVP Limitations and Non-Goals](#17-mvp-limitations-and-non-goals)
18. [Post-MVP Evolution Directions](#18-post-mvp-evolution-directions)
19. [External Dependencies and Assumptions](#19-external-dependencies-and-assumptions)

---

## 1. Boundaries and Responsibilities

### What `ml_api` does

- Executes **online inference** for four use cases: churn, recommendations, forecast, segmentation.
- Serves requests **only from `apps/backend`** (synchronous HTTP).
- Reads feature data from SQL sources via feature repositories.
- Reads `serving.model_registry` to resolve which model artifacts to load.
- Loads serialized sklearn-compatible model artifacts from the filesystem at startup.
- Returns structured prediction results to the caller.

### What `ml_api` does NOT do

- Does not perform ETL, build `mart.*` or `feature.*` tables.
- Does not own train or deploy pipelines.
- Does not write to `serving.model_registry` (read-only consumer).
- Does not run DDL or Alembic migrations (ADR-002).
- Does not serve frontend or BI directly.
- Does not implement batch scoring (that is `jobs/batch_scoring`'s domain).
- Does not write online predictions to `serving.*` tables in MVP.
- Does not implement `MlApiClient` in `apps/backend` (Q6 - external dependency).

### Boundaries with adjacent services

| Adjacent service | Boundary |
|---|---|
| `apps/backend` | Backend owns product-facing API; ml_api owns inference contracts and artifact loading. ml_api receives JSON requests and returns JSON predictions. |
| `jobs/feature_builder` | Builds `feature.*` tables; ml_api only reads them. |
| `jobs/train` | Produces model artifacts and `feature_columns.json`; ml_api only consumes them. |
| `jobs/batch_scoring` | Owns bulk scoring and writes to `serving.*`; ml_api does online-only. |
| PostgreSQL | ml_api is read-only on `feature.*`, `mart.*`, `serving.model_registry`. |
| Artifact volume | ml_api reads from `./artifacts/models` mount; nothing writes to it during serving. |

---

## 2. Use Cases and API Contract

### 2.1 General request model

All four prediction endpoints accept a JSON body and return a unified `StubPredictionResponse` envelope. All request models inherit from `BaseMLRequest`, which carries optional model routing options (post-MVP; ignored in MVP).

```
POST /ml/{use_case}/predict
Content-Type: application/json
← apps/backend (only caller)
```

### 2.2 Response envelope (all endpoints)

```python
class StubPredictionResponse(BaseModel):
    status: str                            # "ok" on success, "error" on failure
    request_type: str                      # "churn" | "recommendations" | "forecast" | "segmentation"
    todo: str                              # empty string on live inference; legacy MVP field
    payload: dict[str, Any]               # business data - see per-use-case shapes below
    trace_payload: dict[str, Any] | None = None  # always None in MVP (Q5)
```

**Key rules:**
- `payload` contains **only business data** for the specific use case.
- `trace_payload` is `None` in MVP; no feature-flag plumbing is built in MVP. The field is present in the schema now (non-breaking optional, Q5) so the backend contract already includes it.
- `model_name`, `model_version`, and other technical metadata are **not** placed in `payload`. They go into `trace_payload` when enabled (post-MVP).
- The mapping from internal domain results to `payload` is performed by a dedicated mapping step in the application layer - this is the single place encoding the JSON contract to `apps/backend`.

### 2.3 Use Case 1 - Churn prediction

**Endpoint:** `POST /ml/churn/predict`

**Request:**
```python
class ChurnPredictionRequest(BaseMLRequest):
    user_id: str
    as_of_date: date | None = None
```

**MVP behavior of `as_of_date`:** Validated (must be a valid date if provided) and logged. Does **not** drive historical feature slice selection in MVP, because historical feature slices are not yet available. Post-MVP: when historical `feature.churn` rows by date exist, the repository can be extended to filter by `as_of_date` without changing the external API.

**Payload (Q1 decision):**
```json
{
  "churn_probability": 0.87,
  "churn_bucket": "high",
  "top_factors": [
    {"feature": "days_since_last_purchase", "direction": "risk_up"},
    {"feature": "rfm_segment", "direction": "risk_up"}
  ]
}
```

- `churn_probability`: float in [0.0, 1.0] - output of `model.predict_proba(X)[0, 1]`.
- `churn_bucket`: `"low"` | `"medium"` | `"high"` - derived from probability thresholds (e.g. ≥0.7 → high, 0.4–0.7 → medium, <0.4 → low).
- `top_factors`: `list[{feature: str, direction: str}] | None` - optional field (Q2). In MVP may be `None` or populated by simple heuristics (e.g. most deviated features from mean). Full SHAP-based explainability is post-MVP.

### 2.4 Use Case 2 - Recommendations

**Endpoint:** `POST /ml/recommendations/predict`

**Request:**
```python
class RecommendationsRequest(BaseMLRequest):
    user_id: str
    limit: int = Field(default=5, ge=1, le=50)
```

**Payload (Q1 decision):**
```json
{
  "items": [
    {"item_id": "SKU123", "score": 0.91, "reason": "similar_to_recent_purchases"},
    {"item_id": "SKU456", "score": 0.88, "reason": null}
  ]
}
```

- `items`: list of `RecommendationItem` objects, truncated to `limit`.
- `item_id`: required string identifier.
- `score`: `float | None` - acceptable to be `None` in MVP if the model returns only ranked IDs.
- `reason`: `str | None` - acceptable to be `None` in MVP; simple heuristic string is sufficient if model does not produce reasons.

### 2.5 Use Case 3 - Sales forecast

**Endpoint:** `POST /ml/forecast/predict`

**Request:**
```python
class ForecastRequest(BaseMLRequest):
    entity_id: str = "all"   # e.g. "all", "store:42", "category:electronics"
    horizon_days: int = Field(default=30, ge=1, le=365)
```

**Payload:**
```json
{
  "forecast": [
    {"date": "2026-04-08", "value": 12500.0},
    {"date": "2026-04-09", "value": 13100.0}
  ]
}
```

- `forecast`: list of `ForecastPoint` objects of length `horizon_days`.
- `date`: ISO date string for each future day.
- `value`: predicted revenue/volume float.

### 2.6 Use Case 4 - Segmentation

**Endpoint:** `POST /ml/segmentation/predict`

**Request:**
```python
class SegmentationRequest(BaseMLRequest):
    user_id: str
    segment_scope: Literal["customer"] = "customer"
```

**MVP note:** `user_id` is required in MVP. The `null user_id` aggregate path is unspecified and will raise `FeaturesNotFoundError` until the semantics are clarified.

**Payload:**
```json
{
  "segment": "high_value_loyal",
  "details": {
    "rfm_code": "555",
    "cluster_id": 3
  }
}
```

- `segment`: string label derived from the cluster ID via a label map.
- `details`: optional `SegmentationDetails` with `rfm_code: str | None` and `cluster_id: int | None`.

### 2.7 Inference request flow

```
apps/backend
  → POST /ml/{use_case}/predict
      ↓
FastAPI router (deserialize + validate request)
      ↓
use case service (via Depends)
  1. Read feature DTO from feature repository
  2. Resolve model_name via ModelNameResolver
  3. Get active version from ModelRegistryRepository
  4. Map feature DTO → model input array (using feature_columns.json)
  5. Call RuntimeManager.predict_{use_case}(features, options)
  6. Map raw prediction → domain result DTO
  7. Map domain result DTO → payload Pydantic model
  8. Wrap in StubPredictionResponse
      ↓
FastAPI router (serialize + return HTTP 200)
      ↓
apps/backend receives response
```

### 2.8 HTTP contract summary

| Endpoint | Method | Request body type | Success code | Failure codes |
|---|---|---|---|---|
| `/ml/churn/predict` | POST | `ChurnPredictionRequest` | 200 | 404 (no features), 503 (no model), 500 (inference error) |
| `/ml/recommendations/predict` | POST | `RecommendationsRequest` | 200 | 404, 503, 500 |
| `/ml/forecast/predict` | POST | `ForecastRequest` | 200 | 404, 503, 500 |
| `/ml/segmentation/predict` | POST | `SegmentationRequest` | 200 | 404, 503, 500 |
| `/ml/health` | GET | - | 200 | - |
| `/ml/ready` | GET | - | 200 | 503 |

---

## 3. Architectural Style and Layers

### 3.1 Overall style

`apps/ml_api` uses a **layered / clean architecture** with explicit dependency direction rules. The layers are:

```
api → application → domain ← infrastructure
                           ← runtime
cross_cutting (used by all layers, no business logic)
dependencies (wiring layer)
```

### 3.2 Layer descriptions

**API layer** (`api/`)
- FastAPI routers and Pydantic request/response schemas.
- Deserializes requests, calls application services via `Depends()`, serializes responses.
- Contains centralized exception handlers in `api/errors.py`.
- Must NOT contain: business logic, SQL, model loading, per-endpoint `try/except` for domain errors.

**Application / Service layer** (`application/services/`)
- Orchestrates the ML inference use case pipeline.
- Calls feature repositories, `ModelNameResolver`, `ModelRegistryRepository`, and `RuntimeManager`.
- Maps feature DTOs → model inputs; maps raw predictions → domain result DTOs.
- Maps domain result DTOs → Pydantic payload models (this is the **adapter/mapping step** - single point for JSON contract encoding, Q decision).
- Must NOT depend on FastAPI, HTTP objects, or raw SQL.
- Must NOT manage lifecycle of DB engine, session factory, or models.

**Domain layer** (`domain/`)
- Defines protocols (interfaces) for repositories and RuntimeManager.
- Defines internal data contracts: feature DTOs, `ModelVersionInfo`, domain result DTOs, domain exceptions.
- Has no external dependencies (no FastAPI, no SQLAlchemy, no sklearn).

**Infrastructure layer** (`infrastructure/`)
- Concrete implementations of domain repository protocols.
- Feature repositories: read SQL from `feature.*` (target) or `mart.*` (MVP fallback).
- Model registry repository: reads `serving.model_registry`.
- DB session factory helpers using `common.db.postgres.create_db_engine()`.
- Adapters to `libs/common`.

**Runtime layer** (`runtime/`)
- `loaders.py`: loads model artifacts (`model.pkl`) and `feature_columns.json` from disk.
- `manager_impl.py`: implements `RuntimeManager` protocol; holds loaded models in memory; provides `predict_*` methods per use case.
- Does not depend on FastAPI, HTTP, or SQL.

**Cross-cutting layer** (`cross_cutting/`)
- Logging helpers, metrics emit wrappers, tracing stubs.
- Used by all layers; contains no business logic.

**Dependencies layer** (`dependencies/`)
- `container.py`: FastAPI `Depends()` factory functions that assemble services from `app.state`.

### 3.3 Lifecycle management

- Heavy singleton dependencies (DB engine, session factory, `RuntimeManager`) are created **once in `lifespan`** in `main.py`.
- Stored on `app.state` and injected via `Depends()`.
- Service layer instances are created per request via providers.
- Services never manage model lifecycle or DB engine lifecycle.

### 3.4 Patterns used

| Pattern | Applied to |
|---|---|
| Service Layer | `ChurnPredictionService`, `RecommendationsService`, `ForecastService`, `SegmentationService` |
| Repository | `ChurnFeatureRepository`, `RecommendationsFeatureRepository`, `ForecastFeatureRepository`, `SegmentationFeatureRepository`, `ModelRegistryRepository` |
| Dependency Injection | FastAPI `Depends()` in all routers; constructor injection in services |
| Adapter | RuntimeManager hides sklearn/pickle model format; per-use-case `predict_*` methods |
| Protocol (structural subtyping) | All domain interfaces are `typing.Protocol` - enables test doubles without inheritance |

**Patterns explicitly NOT used:**
- Unit of Work (ml_api is read-heavy; no complex write transactions).
- Full DDD (no aggregate roots, domain events, rich entities).
- Redis / distributed cache (post-MVP).

### 3.5 Key dependency rules

**Allowed:**
- `api` → `application`, `domain`, `dependencies`
- `application` → `domain`
- `infrastructure` → `domain`, `libs/common`
- `runtime` → `domain`, `libs/common`

**Forbidden:**
- `application` → FastAPI request/response objects
- `domain` → anything outside `domain/`
- `infrastructure` → `application`
- `runtime` → `infrastructure` or `api`
- `api` → raw SQL
- `api` → direct artifact loading

---

## 4. Feature Data and Feature Repositories

### 4.1 Principles

- Each use case has its **own feature repository file** and its own domain protocol.
- Repositories return **typed DTOs**, not `dict[str, Any]`. This makes the feature contract explicit, enables IDE completion, and catches missing keys at object construction time.
- SQL is encapsulated inside infrastructure implementations; application layer never sees raw SQL.
- The boundary between feature DTO and model input is explicit: the application service performs the mapping using `feature_columns.json` (Q3).

### 4.2 Target vs. MVP data sources

| Use case | Target source | MVP source |
|---|---|---|
| Churn | `feature.churn` | `mart.customer_360` + `mart.rfm` + `mart.behavior_metrics` |
| Recommendations | `feature.recsys` | `mart.customer_360` |
| Forecast | `feature.forecast` | `mart.sales_daily` |
| Segmentation | `feature.segmentation` | `mart.customer_360` + `mart.rfm` |

**Fallback rule (Q3 enabler):** Each feature repository implementation uses an explicit fallback pattern:

```python
def get_features_for_user(self, user_id: str, ...) -> ChurnFeatures | None:
    # Primary: feature.churn (target)
    try:
        row = conn.execute(text("SELECT * FROM feature.churn WHERE user_id = :uid"), ...).one_or_none()
        if row is not None:
            logger.debug("feature_source=feature.churn user_id=%s", user_id)  # ← visible in logs
            return ChurnFeatures(**dict(row))
    except ProgrammingError:
        pass  # table not yet populated
    # Fallback: mart.*
    row = conn.execute(text("SELECT c.*, r.* FROM mart.customer_360 c LEFT JOIN mart.rfm r USING (user_id) WHERE c.user_id = :uid"), ...).one_or_none()
    if row is None:
        return None
    logger.debug("feature_source=mart_fallback user_id=%s", user_id)  # ← logged on every fallback
    return ChurnFeatures(**dict(row))
```

The DEBUG log on every request makes it straightforward to confirm when teams switch from mart fallback to real feature tables.

### 4.3 Feature column ordering contract (Q3)

**Problem:** sklearn models are sensitive to column order. If `ml_api` builds the input array in a different column order than `jobs/train` used, inference silently produces wrong results.

**Solution (Q3 decision):**
- Every model artifact directory contains **both** `model.pkl` **and** `feature_columns.json`.
- `feature_columns.json` defines the exact ordered list of feature column names for that model.
- `RuntimeManager` loads `feature_columns.json` at startup alongside the model.
- The application service uses the columns list to build the model input array from the typed feature DTO.
- Column order is **never hardcoded** in Python application code.

```json
// artifacts/models/churn_model/v1/feature_columns.json
["days_since_last_order", "orders_count", "total_revenue", "recency_score", "frequency_score", "monetary_score", "event_count", "session_count", "days_since_last_event"]
```

```python
# In application service, build input array from DTO + columns list:
def _build_model_input(self, features: ChurnFeatures, feature_columns: list[str]) -> np.ndarray:
    row = [float(getattr(features, col, None) or 0.0) for col in feature_columns]
    return np.array([row])
```

For MVP, `feature_columns.json` may be created manually. Long-term, `jobs/train` is responsible for generating it automatically alongside `model.pkl`. Regardless of authorship, it is a **required artifact** - if missing at startup, the model must not be loaded and an error must be logged.

### 4.4 `as_of_date` in churn feature retrieval

- The domain protocol for `ChurnFeatureRepository` includes `as_of_date: date | None` as a parameter.
- In MVP, implementations accept but ignore `as_of_date` (no historical feature slices available).
- Post-MVP: when historical feature data is available, the SQL can be extended to filter by `as_of_date` without changing the interface or the external API.

### 4.5 Behavior when features are not found

| Condition | Behavior |
|---|---|
| Repository returns `None` for `user_id` | Service raises `FeaturesNotFoundError` → HTTP 404 |
| Repository returns DTO with some `None` fields | Service applies defaults (e.g. 0.0) for non-critical fields; raises error if critical fields absent |
| `feature.*` table missing (`ProgrammingError`) | Fallback to `mart.*`; if also empty → 404 |

---

## 5. Shared Utils and Common Components

`ml_api` reuses the following from `libs/common`:

| Utility | Import path | What it provides |
|---|---|---|
| Settings | `common.config.settings.get_settings()` | `AppSettings`: `postgres_dsn`, `model_artifacts_path`, `app_log_level` |
| DB engine | `common.db.postgres.create_db_engine()` | `sqlalchemy.Engine` with `pool_pre_ping=True` |
| Logging | `common.logging.setup.configure_logging()` | Root logger configuration; called once in lifespan |
| Metrics | `common.metrics.registry.emit_counter()` | Counter stub; interface compatible with future Prometheus integration |
| Filesystem | `common.utils.filesystem.ensure_directory()` | `mkdir -p` wrapper |

**What `ml_api` does NOT duplicate:**
- Logger implementation or configuration.
- Config reading logic (delegates fully to `AppSettings`).
- DB engine creation (calls `create_db_engine()`, never constructs its own).
- Metrics interface definition.

---

## 6. Model Registry and Model Versioning

### 6.1 `serving.model_registry` table

The canonical schema is defined by the backend Alembic migration:

| Column | Type | Notes |
|---|---|---|
| `id` | int/uuid | PK |
| `model_name` | str | Technical name, e.g. `"churn_model"` |
| `model_version` | str | e.g. `"v1"`, `"2026-04-07"` |
| `stage` | str | e.g. `"production"` - for future use |
| `artifact_path` | str | Relative path to artifact dir, e.g. `"churn_model/v1"` |
| `is_active` | bool | True = currently active and should be loaded |
| `created_at` | datetime | Row creation timestamp |

**Important:** `use_case` and `model_key` are **not** columns in this table. They belong to the resolver layer.

### 6.2 Ownership (Q4 decision)

- `ml_api` is a **read-only consumer** of `serving.model_registry`.
- `ml_api` never creates, updates, or seeds registry rows.
- **Ownership of seeding** belongs to `apps/backend` / platform/infra.
- `ml_api` assumes rows exist before startup. If no active models are found at startup, `/ml/ready` returns 503 and the service is considered not ready.

### 6.3 Domain contracts

**`ModelVersionInfo` DTO:**
```python
class ModelVersionInfo(BaseModel):
    model_name: str
    model_version: str
    stage: str
    artifact_path: str
    is_active: bool
    created_at: datetime
```

**`ModelRegistryRepository` protocol:**
```python
class ModelRegistryRepository(Protocol):
    def get_active_model_version(self, model_name: str) -> ModelVersionInfo | None: ...
    def list_model_versions(self, model_name: str) -> list[ModelVersionInfo]: ...
```

Selection rule when multiple active rows exist for a `model_name`: sort by `model_version` descending, then `created_at` descending; take first row.

### 6.4 `ModelNameResolver`

Decouples the API/use-case vocabulary from the registry vocabulary:

```python
class ModelNameResolver(Protocol):
    def resolve(self, use_case: str, model_key: str | None = None) -> str: ...
```

**MVP implementation (`StaticModelNameResolver`):**
```python
class StaticModelNameResolver:
    _MAP = {
        "churn": "churn_model",
        "recommendations": "recsys_model",
        "forecast": "forecast_model",
        "segmentation": "segmentation_model",
    }
    def resolve(self, use_case: str, model_key: str | None = None) -> str:
        if use_case not in self._MAP:
            raise ValueError(f"Unknown use case: {use_case}")
        return self._MAP[use_case]
```

In MVP, `model_key` is ignored. The resolver is cheap to implement but makes the mapping explicit and changeable without touching service code.

### 6.5 Artifact path resolution

```
artifact_path in registry: "churn_model/v1"
model_artifacts_path (from settings): "/workspace/artifacts/models"

Full model path: /workspace/artifacts/models/churn_model/v1/model.pkl
feature_columns path: /workspace/artifacts/models/churn_model/v1/feature_columns.json
```

Both files must exist. If either is missing, the model is skipped at startup with an `ERROR` log.

### 6.6 Version promotion workflow

1. Train new model; save artifacts at `artifacts/models/{model}/v2/model.pkl` + `feature_columns.json`.
2. INSERT new row in `serving.model_registry` with `is_active = TRUE`.
3. UPDATE old row to `is_active = FALSE`.
4. Restart `ml-api` container - picks up new row at startup.

No hot-reload; no per-request registry re-query. Container restart is the designed upgrade mechanism.

---

## 7. Logging

### 7.1 Setup

- Each module uses a per-module logger: `logger = logging.getLogger(__name__)`.
- `configure_logging(settings.app_log_level)` from `libs/common` is called once in `main.py` lifespan before any other setup.
- Default log level: `INFO`. Debug-level messages use `DEBUG`.

### 7.2 Mandatory log events

| Event | Level | Key fields |
|---|---|---|
| Startup: registry query started | INFO | - |
| Startup: model loaded successfully | INFO | `model_name`, `model_version`, `artifact_path`, `load_time_ms` |
| Startup: `feature_columns.json` loaded | INFO | `model_name`, `num_columns` |
| Startup: registry table not found / empty | WARNING | - |
| Startup: artifact file missing | ERROR | `model_name`, `path` |
| Startup: artifact load failure | ERROR | `model_name`, `path`, exception info |
| Startup: `feature_columns.json` missing | ERROR | `model_name`, `path` |
| Startup: no models loaded | WARNING | - |
| Per-request: inference success | INFO | `use_case`, `latency_ms` (no user_id at INFO) |
| Per-request: feature source used | DEBUG | `use_case`, `feature_source` (`feature.churn` or `mart_fallback`) |
| Per-request: `as_of_date` provided | DEBUG | `use_case`, `as_of_date` |
| Per-request: features not found | WARNING | `use_case` (no user_id at WARNING) |
| Per-request: inference failure | ERROR + exc_info | `use_case`, `model_name` |
| Per-request: model not loaded | ERROR | `model_name` |

### 7.3 PII rules

- `user_id` and `entity_id` must **not** appear in logs at `INFO` or `WARNING` level.
- `user_id` may appear at `DEBUG` level only (disabled in production by log level).
- Raw feature values (individual column values) must **never** be logged.
- No DB DSN, file paths with credentials, or internal stack traces in external-facing error responses.

---

## 8. Metrics, Tracing, Observability

### 8.1 Metrics

All metrics use `emit_counter()` from `common.metrics.registry`. The interface is compatible with a future Prometheus integration - only the function body changes.

**Counters:**

```python
emit_counter("ml.requests.total",          1, use_case="churn", outcome="success")
emit_counter("ml.requests.total",          1, use_case="churn", outcome="business_error")
emit_counter("ml.requests.total",          1, use_case="churn", outcome="infra_error")
emit_counter("ml.business_errors.total",   1, use_case="churn", error_type="features_not_found")
emit_counter("ml.business_errors.total",   1, use_case="churn", error_type="no_active_model")
emit_counter("ml.model_errors.total",      1, use_case="churn", error_type="runtime")
emit_counter("ml.model_errors.total",      1, use_case="churn", error_type="loading_failure")
emit_counter("ml.startup.model_loaded",    1, model_name="churn_model")
```

**Latency:** Measured with `time.monotonic()` at the service boundary. Logged at `INFO` as `latency_ms`. Actual metrics histogram is a post-MVP concern (requires a real metrics backend).

### 8.2 Where metrics are emitted

- **HTTP middleware:** total request count, HTTP-level latency, outcome category.
- **Feature repositories:** `business_errors.total{error_type="features_not_found"}`, DB error counters.
- **RuntimeManager:** model inference latency, `model_errors.total`.
- **Service layer:** does NOT call `emit_counter` directly. Metrics are at layer boundaries.

### 8.3 `trace_payload` (Q5 decision)

- `trace_payload: dict[str, Any] | None = None` is present in `StubPredictionResponse`.
- In MVP, it is **always `None`**. No feature-flag plumbing, no `request_id`/`correlation_id` middleware, no population logic required.
- Post-MVP: feature flags (`include_trace_payload_in_response`, `include_model_metadata_in_trace_payload`) control population with `request_id`, `model_name`, `model_version`, etc.

### 8.4 `request_id` / `correlation_id`

- MVP: not implemented in middleware.
- Post-MVP: `X-Request-Id` and `X-Correlation-Id` headers read by middleware; included in log records and optionally in `trace_payload`.

---

## 9. Pydantic Schemas

### 9.1 Base schemas

```python
from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, Field


class StubPredictionResponse(BaseModel):
    status: str
    request_type: str
    todo: str
    payload: dict[str, Any]
    trace_payload: dict[str, Any] | None = None  # always None in MVP (Q5)


class ModelRoutingOptions(BaseModel):
    model_key: str | None = Field(default=None)      # post-MVP: alias for model selection
    model_version: str | None = Field(default=None)  # post-MVP: explicit version pin


class BaseMLRequest(BaseModel):
    options: ModelRoutingOptions | None = Field(default=None)
```

### 9.2 Churn schemas

```python
class ChurnPredictionRequest(BaseMLRequest):
    user_id: str
    as_of_date: date | None = None


class TopFactor(BaseModel):
    feature: str
    direction: str   # e.g. "risk_up", "risk_down"


class ChurnPredictionPayload(BaseModel):
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    churn_bucket: Literal["low", "medium", "high"]
    top_factors: list[TopFactor] | None = None   # optional (Q1, Q2)
```

### 9.3 Recommendations schemas

```python
class RecommendationsRequest(BaseMLRequest):
    user_id: str
    limit: int = Field(default=5, ge=1, le=50)


class RecommendationItem(BaseModel):
    item_id: str
    score: float | None = None    # may be None in MVP (Q1)
    reason: str | None = None     # may be None in MVP (Q1)


class RecommendationsPayload(BaseModel):
    items: list[RecommendationItem]
```

### 9.4 Forecast schemas

```python
class ForecastRequest(BaseMLRequest):
    entity_id: str = "all"
    horizon_days: int = Field(default=30, ge=1, le=365)


class ForecastPoint(BaseModel):
    date: date
    value: float


class ForecastPayload(BaseModel):
    forecast: list[ForecastPoint]
```

### 9.5 Segmentation schemas

```python
class SegmentationRequest(BaseMLRequest):
    user_id: str
    segment_scope: Literal["customer"] = "customer"


class SegmentationDetails(BaseModel):
    rfm_code: str | None = None
    cluster_id: int | None = None


class SegmentationPayload(BaseModel):
    segment: str
    details: SegmentationDetails | None = None
```

### 9.6 Mapping layer

The application service builds the payload Pydantic model from the domain result DTO, then serializes it into `StubPredictionResponse.payload`:

```python
# In ChurnPredictionService.predict():
domain_result = self._run_inference(features)
payload_model = ChurnPredictionPayload(
    churn_probability=domain_result.probability,
    churn_bucket=self._bucket(domain_result.probability),
    top_factors=domain_result.top_factors,
)
return StubPredictionResponse(
    status="ok",
    request_type="churn",
    todo="",
    payload=payload_model.model_dump(),
    trace_payload=None,
)
```

This mapping step is the **single place** encoding the JSON contract to `apps/backend`. Future changes in external contract (field renames, additions) only touch this mapping, not the domain or inference logic.

---

## 10. Package and File Structure

```text
apps/ml_api/
│
├── main.py
│     CREATE/MODIFY: lifespan (registry + artifact loading), exception handler registration
│
├── api/
│   ├── __init__.py
│   ├── errors.py                         NEW: centralized exception handlers
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                     MODIFY: add GET /ml/ready
│   │   ├── churn.py                      NEW: POST /ml/churn/predict
│   │   ├── recommendations.py            NEW: POST /ml/recommendations/predict
│   │   ├── forecast.py                   NEW: POST /ml/forecast/predict
│   │   └── segmentation.py              NEW: POST /ml/segmentation/predict
│   └── schemas/
│       ├── __init__.py
│       ├── base.py                       MODIFY: StubPredictionResponse + trace_payload, BaseMLRequest, ModelRoutingOptions
│       ├── churn.py                      NEW: ChurnPredictionRequest, TopFactor, ChurnPredictionPayload
│       ├── recommendations.py            NEW: RecommendationsRequest, RecommendationItem, RecommendationsPayload
│       ├── forecast.py                   NEW: ForecastRequest, ForecastPoint, ForecastPayload
│       └── segmentation.py              NEW: SegmentationRequest, SegmentationDetails, SegmentationPayload
│
├── application/
│   └── services/
│       ├── __init__.py
│       ├── churn_service.py              NEW: ChurnPredictionService.predict()
│       ├── recommendations_service.py    NEW: RecommendationsService.predict()
│       ├── forecast_service.py           NEW: ForecastService.predict()
│       └── segmentation_service.py      NEW: SegmentationService.predict()
│
├── domain/
│   ├── __init__.py
│   ├── exceptions.py                     NEW: MlApiError hierarchy
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── features.py                   NEW: ChurnFeatures, RecommendationsUserFeatures, ForecastHistory, SegmentationFeatures
│   │   ├── predictions.py                NEW: ChurnResult, RecommendationResult, ForecastResult, SegmentationResult (internal)
│   │   └── registry.py                  NEW: ModelVersionInfo
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── features.py                   NEW: Protocol definitions for 4 feature repositories
│   │   └── model_registry.py            NEW: ModelRegistryRepository protocol
│   └── runtime/
│       ├── __init__.py
│       └── manager.py                   NEW: RuntimeManager protocol + ModelNameResolver protocol
│
├── infrastructure/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py                   NEW: session factory helper
│   └── repositories/
│       ├── __init__.py
│       ├── features/
│       │   ├── __init__.py
│       │   ├── churn_pg.py               NEW: ChurnFeatureRepositoryImpl
│       │   ├── recommendations_pg.py     NEW: RecommendationsFeatureRepositoryImpl
│       │   ├── forecast_pg.py            NEW: ForecastFeatureRepositoryImpl
│       │   └── segmentation_pg.py       NEW: SegmentationFeatureRepositoryImpl
│       └── model_registry/
│           ├── __init__.py
│           └── registry_pg.py           NEW: ModelRegistryRepositoryImpl
│
├── runtime/
│   ├── __init__.py
│   ├── loaders.py                        NEW: load_pickle_artifact(), load_feature_columns()
│   └── manager_impl.py                  NEW: RuntimeManagerImpl (holds models, predict_* methods)
│
├── cross_cutting/
│   ├── __init__.py
│   ├── logging.py                        NEW: logging helpers (e.g. log_inference_result)
│   ├── metrics.py                        NEW: emit_* wrappers
│   └── tracing.py                       NEW: trace stubs (post-MVP population)
│
└── dependencies/
    ├── __init__.py
    └── container.py                     NEW: get_churn_service(), get_recommendations_service(), etc.
```

**Total new files:** ~28. **Modified files:** `main.py`, `api/schemas/base.py`, `api/routers/health.py`. No existing files deleted.

**Test structure (adjacent to `apps/ml_api/`):**

```text
tests/
├── unit/
│   ├── services/        # test service layer with Protocol mocks
│   ├── runtime/         # test loaders, manager_impl
│   └── resolver/        # test StaticModelNameResolver
├── integration/
│   └── repositories/    # test repos against real DB
└── contract/
    └── endpoints/       # TestClient contract tests per endpoint
```

---

## 11. Runtime Manager and Model Loading

### 11.1 `RuntimeManager` protocol

Defined in `domain/runtime/manager.py`:

```python
class RuntimeManager(Protocol):
    def predict_churn(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_recommendations(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_forecast(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def predict_segmentation(
        self, features: dict[str, Any], options: ModelRoutingOptions | None
    ) -> dict[str, Any]: ...

    def loaded_use_cases(self) -> list[str]: ...
```

- `features` is a `dict` prepared from the typed feature DTO using `feature_columns.json`.
- Return value is a raw prediction dict (scores, labels, etc.). The application service maps it to a typed payload.
- `RuntimeManager` has no knowledge of Pydantic, HTTP, or SQL.

### 11.2 `RuntimeManagerImpl`

In `runtime/manager_impl.py`. Holds loaded models and their `feature_columns` lists:

```python
class RuntimeManagerImpl:
    def __init__(self) -> None:
        self._models: dict[str, Any] = {}           # model_name → loaded sklearn object
        self._feature_columns: dict[str, list[str]] = {}  # model_name → column list

    def register(self, model_name: str, model: Any, feature_columns: list[str]) -> None:
        self._models[model_name] = model
        self._feature_columns[model_name] = feature_columns

    def predict_churn(self, features: dict[str, Any], options: ...) -> dict[str, Any]:
        model = self._get_model("churn_model")
        cols = self._feature_columns["churn_model"]
        X = np.array([[float(features.get(c) or 0.0) for c in cols]])
        proba = model.predict_proba(X)[0, 1]
        return {"probability": float(proba)}
    # ... similar for other use cases
```

### 11.3 Startup sequence (lifespan in `main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.app_log_level)
    engine = create_db_engine()
    app.state.db_engine = engine

    resolver = StaticModelNameResolver()
    registry_repo = ModelRegistryRepositoryImpl(engine)
    runtime = RuntimeManagerImpl()

    known_use_cases = ["churn", "recommendations", "forecast", "segmentation"]
    for use_case in known_use_cases:
        model_name = resolver.resolve(use_case)
        version_info = registry_repo.get_active_model_version(model_name)
        if version_info is None:
            logger.warning("No active model for use_case=%s model_name=%s", use_case, model_name)
            continue
        artifact_dir = settings.model_artifacts_path / version_info.artifact_path
        try:
            model = load_pickle_artifact(artifact_dir / "model.pkl")
            feature_columns = load_feature_columns(artifact_dir / "feature_columns.json")  # Q3
            runtime.register(model_name, model, feature_columns)
            logger.info("loaded model_name=%s model_version=%s", model_name, version_info.model_version)
        except (FileNotFoundError, Exception) as exc:
            logger.error("failed to load model_name=%s: %s", model_name, exc)

    app.state.runtime = runtime
    app.state.resolver = resolver
    app.state.registry_repo = registry_repo

    if not runtime.loaded_use_cases():
        logger.warning("No models loaded - all prediction endpoints will return 503")

    yield

    engine.dispose()
```

### 11.4 Graceful degradation

| Condition | Behavior |
|---|---|
| `serving.model_registry` table missing | Catch `ProgrammingError`, log WARNING, continue with no models loaded |
| Table exists, zero active rows for a use case | Log WARNING, continue; that use case will return 503 |
| `model.pkl` file missing | Log ERROR, skip that model; others load normally |
| `feature_columns.json` missing (Q3) | Log ERROR, skip that model (cannot safely build input) |
| `model.pkl` unpickling fails | Log ERROR, skip; others load normally |
| All models missing | Log WARNING; `/ml/ready` → 503 |
| DB engine connection fails | Propagate exception → container restart is appropriate |

### 11.5 Artifact loading functions

```python
# runtime/loaders.py

def load_pickle_artifact(path: Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)

def load_feature_columns(path: Path) -> list[str]:
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(c, str) for c in data):
        raise ValueError(f"feature_columns.json must be a list[str]: {path}")
    return data
```

---

## 12. SQL Contracts and Repository Interfaces

### 12.1 Feature repository protocols (domain layer)

```python
class ChurnFeatureRepository(Protocol):
    def get_features_for_user(
        self, user_id: str, as_of_date: date | None = None
    ) -> ChurnFeatures | None: ...

class RecommendationsFeatureRepository(Protocol):
    def get_user_features(self, user_id: str) -> RecommendationsUserFeatures | None: ...

class ForecastFeatureRepository(Protocol):
    def get_timeseries_for_entity(
        self, entity_id: str, history_window: int | None = None
    ) -> ForecastHistory | None: ...

class SegmentationFeatureRepository(Protocol):
    def get_features_for_user(self, user_id: str) -> SegmentationFeatures | None: ...
```

These interfaces are stable and do not change when the SQL source switches from `mart.*` to `feature.*`.

### 12.2 Feature DTO definitions (domain layer)

```python
# domain/dto/features.py

class ChurnFeatures(BaseModel):
    user_id: str
    days_since_last_order: float | None
    orders_count: float | None
    total_revenue: float | None
    recency_score: float | None
    frequency_score: float | None
    monetary_score: float | None
    event_count: float | None
    session_count: float | None
    days_since_last_event: float | None
    # additional fields are accepted and ignored (extra="allow")

class RecommendationsUserFeatures(BaseModel):
    user_id: str
    # user-level profile fields relevant to recsys model
    # exact fields determined by feature.recsys schema

class ForecastHistory(BaseModel):
    entity_id: str
    time_series: list[dict[str, Any]]  # list of {date, revenue, ...} rows

class SegmentationFeatures(BaseModel):
    user_id: str
    rfm_score: float | None
    rfm_segment: str | None
    # RFM metrics, behavioral aggregates
```

### 12.3 MVP SQL patterns

**Churn - primary (feature.churn):**
```sql
SELECT * FROM feature.churn WHERE user_id = :uid LIMIT 1
```

**Churn - mart fallback:**
```sql
SELECT c.user_id, c.orders_count, c.total_revenue, c.days_since_last_order,
       r.recency_score, r.frequency_score, r.monetary_score, r.rfm_score, r.rfm_segment,
       b.event_count, b.session_count, b.days_since_last_event
FROM mart.customer_360 c
LEFT JOIN mart.rfm r USING (user_id)
LEFT JOIN mart.behavior_metrics b USING (user_id)
WHERE c.user_id = :uid
LIMIT 1
```

**Model registry query:**
```sql
SELECT DISTINCT ON (model_name)
    model_name, model_version, stage, artifact_path, is_active, created_at
FROM serving.model_registry
WHERE model_name = :model_name
  AND is_active = TRUE
ORDER BY model_name, model_version DESC, created_at DESC
```

### 12.4 Connection management

- DB engine is created once in lifespan, stored on `app.state`.
- Each request opens one connection: `with engine.connect() as conn:` in the service or repository.
- `pool_pre_ping=True` handles stale connections automatically.
- Repositories accept a `Connection` as a parameter; they never create or close connections.
- No ORM models or mapped classes. All queries use `sqlalchemy.text()`.

---

## 13. Error Handling and HTTP Mapping

### 13.1 Exception hierarchy

```python
# domain/exceptions.py

class MlApiError(Exception):
    """Base class for all ml_api domain exceptions."""

# Application errors (4xx)
class FeaturesNotFoundError(MlApiError):
    def __init__(self, use_case: str, key: str) -> None: ...

class NoActiveModelError(MlApiError):
    def __init__(self, use_case: str, model_name: str) -> None: ...

class UnsupportedScopeError(MlApiError):
    def __init__(self, scope: str) -> None: ...

class InvalidRequestDomainError(MlApiError):
    pass

# Infrastructure / runtime errors (5xx)
class RegistryUnavailableError(MlApiError):
    pass

class ArtifactNotFoundError(MlApiError):
    def __init__(self, model_name: str, path: str) -> None: ...

class ModelLoadingError(MlApiError):
    def __init__(self, model_name: str, cause: Exception) -> None: ...

class ModelRuntimeError(MlApiError):
    def __init__(self, use_case: str, cause: Exception) -> None: ...
```

### 13.2 HTTP status mapping

| Exception | HTTP status | `error_code` |
|---|---|---|
| `FeaturesNotFoundError` | 404 Not Found | `FEATURES_NOT_FOUND` |
| `NoActiveModelError` | 503 Service Unavailable | `NO_ACTIVE_MODEL` |
| `UnsupportedScopeError` | 400 Bad Request | `UNSUPPORTED_SCOPE` |
| `InvalidRequestDomainError` | 422 Unprocessable Entity | `INVALID_REQUEST` |
| `RegistryUnavailableError` | 503 Service Unavailable | `REGISTRY_UNAVAILABLE` |
| `ArtifactNotFoundError` | 503 Service Unavailable | `ARTIFACT_NOT_FOUND` |
| `ModelLoadingError` | 503 Service Unavailable | `MODEL_LOADING_ERROR` |
| `ModelRuntimeError` | 500 Internal Server Error | `INFERENCE_ERROR` |
| Any other `Exception` | 500 Internal Server Error | `INTERNAL_ERROR` |

**Why 503 for model-not-ready conditions:** 503 signals to `apps/backend` that this instance cannot currently serve the request, as opposed to 500 which signals an unexpected failure. It correctly tells upstream to retry or fallback.

### 13.3 Error response format

All error responses use `StubPredictionResponse` with `status="error"`:

```json
{
  "status": "error",
  "request_type": "churn",
  "todo": "",
  "payload": {
    "error_code": "FEATURES_NOT_FOUND",
    "error_message": "No features found for the requested entity"
  },
  "trace_payload": null
}
```

No stack traces, file paths, DSN, or internal details in the `error_message`.

### 13.4 Centralized handlers

All handlers are registered in `api/errors.py` via `app.add_exception_handler()`. No per-endpoint `try/except` for domain errors.

```python
# Pseudo-code for handler registration in main.py / api/errors.py

app.add_exception_handler(FeaturesNotFoundError,   handle_features_not_found)   # 404 + WARNING log
app.add_exception_handler(NoActiveModelError,      handle_no_active_model)       # 503 + ERROR log
app.add_exception_handler(ModelRuntimeError,       handle_model_runtime_error)   # 500 + ERROR + exc_info
app.add_exception_handler(MlApiError,              handle_ml_api_error)          # catch-all for subtypes
app.add_exception_handler(Exception,               handle_unexpected_error)      # 500 + ERROR + exc_info
```

---

## 14. Health and Ready Endpoints

### `GET /ml/health` - Liveness

- Unchanged from current implementation.
- Returns `{"status": "ok"}` and HTTP 200.
- Used by Docker/compose to detect if the process is alive.

### `GET /ml/ready` - Readiness (Q4 decision)

- Checks whether at least one model is loaded in `RuntimeManager`.
- If `runtime.loaded_use_cases()` is empty → HTTP 503 `{"status": "not_ready", "loaded": []}`.
- If at least one model is loaded → HTTP 200 `{"status": "ready", "loaded": ["churn", "recommendations"]}`.

```python
@router.get("/ml/ready")
def ready(request: Request):
    runtime: RuntimeManager = request.app.state.runtime
    loaded = runtime.loaded_use_cases()
    if not loaded:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "loaded": []}
        )
    return {"status": "ready", "loaded": loaded}
```

**Use:** Docker-compose healthcheck, backend startup dependency, operational monitoring. A 503 from `/ml/ready` is the expected condition when the registry has not been seeded yet.

---

## 15. Testing Strategy

### 15.1 Unit tests (`tests/unit/`)

**Service layer:** Constructor-inject Protocol mocks for `ChurnFeatureRepository`, `ModelRegistryRepository`, `RuntimeManager`. No disk access, no DB connection.

```python
def test_churn_service_predict_success():
    mock_feature_repo = MockChurnFeatureRepository(returns=sample_churn_features)
    mock_registry = MockModelRegistryRepository(returns=sample_version_info)
    mock_runtime = MockRuntimeManager(returns={"probability": 0.82})
    service = ChurnPredictionService(mock_feature_repo, mock_registry, mock_runtime, resolver)
    result = service.predict(user_id="u1", as_of_date=None)
    assert result.payload["churn_bucket"] == "high"
```

**RuntimeManager:** Test `predict_*` methods with a real (tiny) sklearn model loaded from a temp pickle file.

**Loaders:** Test `load_pickle_artifact` and `load_feature_columns` with valid and invalid files.

**Resolver:** Test `StaticModelNameResolver.resolve()` for all four use cases and unknown use case.

### 15.2 Integration tests (`tests/integration/`)

- Each feature repository tested against a real PostgreSQL test database (not mocked).
- `ModelRegistryRepositoryImpl` tested against a test DB with seeded rows.
- Tests verify: successful query, not-found case, fallback from `feature.*` to `mart.*`.
- DB schema is created by Alembic migrations run in test setup.

### 15.3 Contract tests (`tests/contract/`)

- FastAPI `TestClient` for each endpoint.
- Cover: valid request → 200 with expected payload structure; missing user → 404; no model → 503.
- Verify `trace_payload` is `None` in all responses.
- Validate that `payload` matches the declared Pydantic payload model shape.

### 15.4 Smoke tests

- Startup smoke test: lifespan runs without exceptions when registry is seeded and artifacts exist.
- Startup negative test: lifespan handles empty registry (no exception; `loaded_use_cases()` returns `[]`).
- `/ml/ready` smoke test: returns 503 when no models loaded; 200 when at least one loaded.

---

## 16. Implementation Plan

Based on `docs/user/03_steps.md`, aligned to the merged architecture:

| Stage | Task | Deliverable |
|---|---|---|
| 0 | Scaffold directory structure | All packages created with `__init__.py`; existing health/predictions routes migrated to new locations without behavior change |
| 1 | Base API schemas | `api/schemas/base.py`: `StubPredictionResponse` + `trace_payload`, `BaseMLRequest`, `ModelRoutingOptions`; empty per-use-case schema files |
| 2 | Domain contracts | `domain/exceptions.py`, `domain/dto/` (feature DTOs, prediction result DTOs, `ModelVersionInfo`), `domain/repositories/` protocols, `domain/runtime/manager.py` protocol |
| 3 | DB wiring | `infrastructure/db/session.py` helpers; engine creation kept in lifespan |
| 4 | Model registry repository | `infrastructure/repositories/model_registry/registry_pg.py` - `get_active_model_version`, `list_model_versions`; unit + integration tests |
| 5 | `ModelNameResolver` | `StaticModelNameResolver` in `domain/` or `runtime/`; unit tests |
| 6 | Runtime loaders | `runtime/loaders.py` - `load_pickle_artifact()`, `load_feature_columns()`; tests with valid/missing files |
| 7 | RuntimeManager | `runtime/manager_impl.py` - `register()`, `predict_*()` per use case using `feature_columns.json`; unit tests with fake models |
| 8 | Lifespan + preload | `main.py` lifespan: settings, engine, registry repo, resolver, RuntimeManager; preload all use cases; smoke test |
| 9 | Churn feature repository | `infrastructure/repositories/features/churn_pg.py`; `ChurnFeatures` DTO; mart fallback; integration test |
| 10 | `ChurnPredictionService` | Full pipeline: feature repo → resolver → registry → runtime → mapping; unit test with mocks |
| 11 | Churn API flow | `api/schemas/churn.py`, `api/routers/churn.py`; contract test; smoke test end-to-end |
| 12 | Recommendations (repeat 9–11) | Feature repo, service, router, schemas; contract test |
| 13 | Churn cross-cutting | Metrics counters in feature repo and RuntimeManager; latency logging in service |
| 14 | Forecast (repeat 9–11) | Feature repo, service, router, schemas |
| 15 | Segmentation (repeat 9–11) | Feature repo, service, router, schemas |
| 16 | Health/ready + error handling | `/ml/ready` endpoint; `api/errors.py` handlers for all exception types; tests |
| 17 | Code review pass | Style, imports, layer boundary compliance, duplication, test coverage |

**Recommended first end-to-end target:** Complete stages 0–11 (churn) before starting recommendations. This validates the full architecture from HTTP to inference before implementing remaining use cases.

---

## 17. MVP Limitations and Non-Goals

The following are explicitly **out of scope for MVP**. They are not technical debt - they are deliberate deferral decisions.

| Limitation | Decision rationale |
|---|---|
| `as_of_date` does not drive historical feature selection | Historical `feature.*` slices do not yet exist |
| `top_factors` may be `None` or use simple heuristics | Full SHAP explainability pipeline not required (Q2) |
| `trace_payload` is always `None` | No feature-flag plumbing needed until observability requirements clarify (Q5) |
| `request_id` / `correlation_id` middleware not implemented | Post-MVP observability concern |
| No write-back to `serving.*` tables | DDL not finalized; `jobs/batch_scoring` is the correct owner |
| `MlApiClient` in `apps/backend` not implemented here | Backend's responsibility; external dependency for e2e tests (Q6) |
| No lazy model loading | Startup load is correct; lazy adds latency unpredictability |
| No multi-model routing via `options.model_key` | No second model exists; architecture supports it but logic is not activated |
| No async SQLAlchemy / asyncpg | Sync engine is correct at educational scale |
| No Redis / distributed prediction cache | No measurable benefit at this load |
| Registry seeding not owned by `ml_api` | Owned by backend/infra (Q4) |
| No shared `libs/common/ml/` with batch_scoring | Premature extraction before batch_scoring exists |
| `stage`-based routing in registry | `is_active` is sufficient for MVP |
| No per-endpoint typed response models in OpenAPI | `payload: dict` is sufficient; typed models are post-MVP documentation improvement |

---

## 18. Post-MVP Evolution Directions

The following improvements are designed for after MVP. The architecture described in this document already accommodates them without structural changes.

### Observability
- Add `request_id` / `correlation_id` middleware; populate `trace_payload` via feature flags.
- Connect `emit_counter` to a real Prometheus / OpenTelemetry backend (only the function body changes).
- Add p95/p99 latency histograms.

### Feature data
- Populate `feature.*` tables in `jobs/feature_builder`; remove mart fallback path from repositories.
- Implement full `as_of_date` filtering in `ChurnFeatureRepository` once historical slices exist.

### Explainability
- Add SHAP integration to `ChurnPredictionService` to populate `top_factors` with real feature importance.
- Alternatively, provide a separate `/ml/churn/explain` endpoint rather than embedding SHAP in the predict path.

### Model serving
- Enable multi-model routing via `options.model_key` in `StaticModelNameResolver`.
- Add lazy loading in `RuntimeManagerImpl` for on-demand model variants.
- Enable `stage`-based routing (canary / shadow) using the `stage` column already in the registry.

### Write-back
- Finalize `serving.*` DDL in Alembic migration.
- Add `ServingWriter` in `infrastructure/` and trigger via `background_tasks.add_task()` after successful inference.

### Shared libraries
- Once `jobs/batch_scoring` stabilizes, extract `artifact_loader.py` and `model_registry.py` into `libs/common/ml/` to avoid duplication.

### Async
- When concurrent request throughput justifies it: switch to `AsyncEngine` + `asyncpg`, convert service methods to `async def`, wrap CPU-bound `predict()` calls with `asyncio.run_in_executor`.

---

## 19. External Dependencies and Assumptions

### Registry seeding (Q4)

`ml_api` assumes `serving.model_registry` is seeded **before the container starts**. Seeding is owned by `apps/backend` / platform/infra and is outside `ml_api`'s scope.

Seed SQL (for reference - executed outside `ml_api`):
```sql
INSERT INTO serving.model_registry (model_name, model_version, stage, artifact_path, is_active)
VALUES
    ('churn_model',        'v1', 'production', 'churn_model/v1',        true),
    ('recsys_model',       'v1', 'production', 'recsys_model/v1',        true),
    ('forecast_model',     'v1', 'production', 'forecast_model/v1',      true),
    ('segmentation_model', 'v1', 'production', 'segmentation_model/v1',  true)
ON CONFLICT DO NOTHING;
```

This seed is **not** run by Alembic (ADR-002). It is a one-shot external step.

### `MlApiClient` in `apps/backend` (Q6)

Implementing `MlApiClient` in `apps/backend` is explicitly outside this document's scope. The HTTP contract defined in Section 2 is the source of truth for the backend to build against.

Assumptions for backend implementation:
- Base URL: `http://ml-api:8001` (Docker-compose service name).
- HTTP client: `httpx.Client` (already in backend requirements).
- All four POST endpoints accept JSON and return `StubPredictionResponse`.
- Non-200 responses contain `StubPredictionResponse` with `status="error"` and `payload.error_code`.

`MlApiClient` is an **external dependency for end-to-end integration tests**.

### Model artifacts

- Each model directory must contain **both** `model.pkl` and `feature_columns.json` (Q3).
- Expected on-disk structure (Docker volume `./artifacts/models → /workspace/artifacts/models`):
  ```
  /workspace/artifacts/models/
  ├── churn_model/v1/
  │   ├── model.pkl
  │   └── feature_columns.json
  ├── recsys_model/v1/
  │   ├── model.pkl
  │   └── feature_columns.json
  ├── forecast_model/v1/
  │   ├── model.pkl
  │   └── feature_columns.json
  └── segmentation_model/v1/
      ├── model.pkl
      └── feature_columns.json
  ```
- Models are sklearn-compatible objects: expose at minimum `.predict(X)` and optionally `.predict_proba(X)`.
- Churn model: `.predict_proba(X)` must return shape `(n, 2)` (binary classification).
- Segmentation model: `.predict(X)` returns integer cluster labels.

### SQL schemas

- `serving.model_registry` must exist and be populated (Alembic migration run by `migrator` service).
- `mart.customer_360`, `mart.rfm`, `mart.behavior_metrics`, `mart.sales_daily` must be populated by `jobs/marts_builder` for the mart fallback path to work.

### Python dependencies

The following must be added to `apps/ml_api/requirements/base.txt` before implementation:
```
numpy
scikit-learn
```

### ADR compliance

- **ADR-002:** `ml_api` must not run DDL or Alembic migrations. All schema changes go through the `migrator` service.
- **ADR-003:** SQL business logic lives in `sql/*` files. Python code does not contain inline analytical SQL that belongs in the `sql/` layer.
- **ADR-004:** `apps/backend` and `apps/ml_api` are separate services and must not be merged.

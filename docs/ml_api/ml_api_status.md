# STATUS_ml_api.md

# Текущее состояние / TODO

## 1. Реализовано

- Слойная архитектура: `api`, `application`, `domain`, `infrastructure`, `runtime`, `crosscutting`, `dependencies`.
- Lifespan‑инициализация:
  - создание DB engine;
  - создание `ModelRegistryRepository` и `ModelNameResolver`;
  - preload моделей всех use case’ов из `serving.model_registry` и артефактов в `RuntimeManager`.
- Полный end‑to‑end для всех четырех use case:
  - `POST /ml/churn/predict`;
  - `POST /ml/recommendations/predict`;
  - `POST /ml/forecast/predict`;
  - `POST /ml/segmentation/predict`;  
  включая: Pydantic‑схемы, application‑сервисы, feature‑репозитории, вызовы `RuntimeManager`, маппинг в payload.
- Feature‑репозитории:
  - churn: primary `feature.churn`, fallback в `mart.customer360` + `mart.rfm` + `mart.behaviormetrics`;
  - recommendations: `feature.recsys` (MVP - `mart.customer360`);
  - forecast: `feature.forecast` (MVP - `mart.sales_daily`);
  - segmentation: `feature.segmentation` (MVP - `mart.customer360` + `mart.rfm`).
- Общий HTTP‑envelope ответа и централизованный маппинг доменных ошибок в HTTP‑коды и `payload.errorCode`.
- Метрики и логирование:
  - счетчики запросов/ошибок через `emit_counter`;
  - логирование startup‑событий (registry, загрузка моделей/feature_columns);
  - логирование источника фич (feature.* vs mart.*) и результатов inference (без PII).
- Health/ready:
  - `GET /ml/health` - liveness;
  - `GET /ml/ready` - readiness по факту загруженных моделей (200/503).

## 2. Сознательно отложено (MVP non‑goals)

- Использование Redis (кэш фич/предсказаний).
- Write‑back онлайн‑предсказаний в `serving.*` таблицы (владелец - batch‑scoring/jobs).
- SHAP/объяснимость и “умные” `top_factors` для churn.
- Многоверсийные модели и продвинутый роутинг (`options.model_key`, stage‑routing, canary/shadow).
- MlApiClient, обвязка и e2e‑тесты на стороне `apps/backend`.
- Registry seeding и demo‑bootstrap (сид таблиц и генерация артефактов находятся вне зоны ответственности ml_api).
- Async‑движок/asyncpg, p95/p99‑метрики, requestid/correlationid‑middleware.

## 3. Ближайшие шаги вокруг ml_api (внешние по отношению к сервису)

- Реализовать и интегрировать MlApiClient в `apps/backend` на базе описанного HTTP‑контракта.
- Определить и зафиксировать стандартный bootstrap:
  - сиды `serving.model_registry`;
  - генерация/копирование модельных артефактов в `model_artifacts_path`;
  - демо‑данные в `mart.*` / `feature.*` для локальных happy‑path тестов.
- Добавить системную observability:
  - подключить `emit_counter` к реальному бекенду метрик;
  - добавить requestid/correlationid‑middleware и трассировку.
- После стабилизации batch‑scoring:
  - вынести общие части работы с артефактами и registry в `libs/common/ml`.
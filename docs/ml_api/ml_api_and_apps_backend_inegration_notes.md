# Integration notes для apps/backend

## 1. Как backend должен вызывать ml_api

- Базовый URL в docker‑окружении: `http://ml-api:8001`.
- Эндпоинты:
  - `POST /ml/churn/predict`
  - `POST /ml/recommendations/predict`
  - `POST /ml/forecast/predict`
  - `POST /ml/segmentation/predict`
  - `GET /ml/health`
  - `GET /ml/ready`
- Все предсказания:
  - `Content-Type: application/json`;
  - ответ всегда в общем envelope (`status`, `request_type`, `todo`, `payload`, `trace_payload`).

Рекомендация: реализовать MlApiClient в apps/backend поверх `httpx` (или аналога) и не ходить в ml_api напрямую из хендлеров.

## 2. Что нужно подготовить в окружении backend

### Postgres и схемы

- Прогнать миграции так, чтобы существовали:
  - `mart.*` (минимум: customer360, rfm, behaviormetrics, sales_daily);
  - `feature.*` (по мере готовности feature‑pipelines);
  - `serving.model_registry`.

### Registry seeding

- Перед стартом ml_api обеспечить в `serving.model_registry` хотя бы одну активную запись для `churn`‑модели (и аналогично для других use case по мере готовности).

Минимальный пример (churn):

```sql
INSERT INTO serving.model_registry
  (model_name, model_version, stage, artifact_path, is_active)
VALUES
  ('churn_model', 'v1', 'production', 'churn_model_v1', true)
ON CONFLICT DO NOTHING;
```

### Артефакты моделей

- В каталоге, который ml_api ожидает в `model_artifacts_path`, должны лежать:

```text
<model_artifacts_path>/
  churn_model_v1/
    model.pkl
    feature_columns.json
  ...
```

- backend/infra отвечает за то, чтобы эти артефакты появились до старта ml_api (train‑jobs, копирование, bootstrap‑скрипты и т.п.).

### Демо‑данные для локальной проверки

- Для локального demo/happy‑path:
  - засеять хотя бы одну строку фич в `feature.churn` или `mart.*` под известным `user_id`;
  - использовать этот `user_id` в вызовах backend → ml_api.

## 3. Как интерпретировать ответы и ошибки

### Health/ready

- `GET /ml/health`:
  - использовать как liveness‑пробу (процесс жив/нет).
- `GET /ml/ready`:
  - 200 — можно отправлять predict‑запросы;
  - 503 — моделей нет или они не загружены, следует временно отключить ml‑функционал и/или ретраить позже.

### Predict‑эндпоинты

- При `status = "ok"`:
  - `payload` содержит бизнес‑данные (probability, bucket, items, forecast, segment и т.п.).
- При `status = "error"`:
  - `payload.errorCode`:
    - `FEATURES_NOT_FOUND` (обычно 404) — нет данных для ключа; это бизнес‑ошибка, а не падение сервиса;
    - `NO_ACTIVE_MODEL`/`MODEL_LOADING_ERROR` (обычно 503) — модель временно недоступна; можно ретраить или деградировать функциональность;
    - `INFERENCE_ERROR`/`INTERNAL_ERROR` (500) — внутренняя ошибка, логировать и маппить в “internal error” наружу.

Рекомендация: в MlApiClient всегда смотреть на комбинацию HTTP‑кода и `payload.errorCode`, а не только на статус строки.

## 4. Что НЕ делает ml_api (важно для ожиданий)

- Не запускает миграции и не создаёт схемы в БД.
- Не сидит registry, `mart.*` и `feature.*`.
- Не генерирует demo‑артефакты моделей.
- Не хранит/не возвращает никакой frontend‑ориентированной модельной логики (это уровень apps/backend).
# Краткая инструкция по запуску

## Предпосылки

- Применены миграции Postgres (есть схемы `mart.*`, `feature.*`, `serving.*`).
- В `serving.model_registry` есть хотя бы одна активная запись для модели.
- В каталоге артефактов лежат `model.pkl` и `feature_columns.json` для этой модели.

## Запуск локально (пример)

```bash
uvicorn apps.ml_api.app.main:app --host 0.0.0.0 --port 8001
```

Основные настройки (через `common.config.settings`):

- `postgres_dsn` - строка подключения к БД.
- `model_artifacts_path` - путь к каталогу с модельными артефактами.

## Базовые проверки

- `GET /ml/health` → 200, если процесс жив.
- `GET /ml/ready`:
  - 200 - хотя бы одна модель загружена;
  - 503 - моделей нет или не удалось загрузить.

## Простейший happy‑path (churn)

1. Убедиться, что в `serving.model_registry` есть активная запись для churn‑модели.
2. Убедиться, что в `<model_artifacts_path>/<artifact_path>/` есть `model.pkl` и `feature_columns.json`.
3. Убедиться, что в `feature.churn` или `mart.*` есть данные по тестовому `user_id`.
4. Отправить `POST /ml/churn/predict` с этим `user_id`.

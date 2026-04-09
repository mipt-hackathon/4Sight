Список документации:
- [Final Serving Architecture](./ml_api_serving_solution_final.md) - итоговая архитектура сервиса `ml_api`. Единственный источник истины для реализации
- [Краткая инструкция по запуску](./ml_api_run.md)
- [Как устроен сервис (схематично)](./ml_api_components.md)
- [Текущее состояние / TODO](./ml_api_status.md)
- [Integration notes для apps/backend](./ml_api_and_apps_backend_inegration_notes.md)

---

### Тестовый запуск и проверка bootstrap‑сценария churn happy‑case

**Для чего это нужно**

Bootstrap‑сценарий для churn подготавливает минимальный набор данных и артефактов, чтобы ml_api можно было поднять “с нуля” и сразу получить успешный churn‑predict по тестовому пользователю

Автоматизирует:
  - сид таблиц `feature.*` нужными строками
  - сид `serving.model_registry` churn‑моделью
  - раскладку моковой `churn_model_v1` (model.pkl + feature_columns.json) в ожидаемый каталог

[Подробное описание запуска bootstrap-сценария](./churn_happy_path.md)

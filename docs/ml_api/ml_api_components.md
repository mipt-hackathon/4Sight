## Компоненты и ответственность

```mermaid
flowchart TD
    %% Внешние системы
    Backend[apps/backend]:::external
    Postgres[(PostgreSQL mart.*, feature.*, serving.*)]:::external
    Artifacts[(FS volume model_artifacts_path)]:::external

    %% Граница сервиса
    subgraph MLAPI[apps/ml_api]
        direction TB

        FastAPIApp[FastAPI app main.py]
        API[API слой api/*]
        AppLayer[Application слой application/*]
        Domain[Domain слой domain/*]
        Infra[Infrastructure слой infrastructure/*]
        Runtime[Runtime слой runtime/*]
        CrossCut[Cross-cutting слой crosscutting/*]
        DI[Dependencies слой container.py]
        ModelRegistry[Model registry репозиторий]
        NameResolver[Model name resolver]
    end

    %% Внешние ↔ ml_api
    Backend -->|HTTP JSON /ml/*| API
    Infra -->|SQL к mart, feature, serving| Postgres
    Runtime -->|чтение model.pkl и feature_columns.json| Artifacts

    %% Внутренние связи

    FastAPIApp --> API
    FastAPIApp --> DI
    FastAPIApp --> CrossCut

    API --> AppLayer
    API --> CrossCut
    API --> DI

    AppLayer --> Domain
    AppLayer --> Infra
    AppLayer --> Runtime
    AppLayer --> ModelRegistry
    AppLayer --> NameResolver
    AppLayer --> CrossCut

    Infra --> CrossCut
    ModelRegistry --> Infra

    Runtime --> CrossCut
    NameResolver --> Runtime

    DI --> AppLayer
    DI --> Infra
    DI --> Runtime
    DI --> ModelRegistry
    DI --> NameResolver

    classDef external fill:#eee,stroke:#555,color:#000
```

- **FastAPI app (`main.py`)** - инициализирует приложение, настраивает lifespan, регистрирует роутеры и exception‑handlers.
- **API‑слой (`api/*`)** - описывает HTTP‑эндпоинты и Pydantic‑схемы запросов/ответов, пробрасывает вызовы в application‑сервисы.
- **Application‑слой (`application/*`)** - оркестрирует use case: читает фичи через репозитории, резолвит модель, вызывает RuntimeManager, маппит результат в payload.
- **Domain‑слой (`domain/*`)** - задает протоколы репозиториев и RuntimeManager, DTO фич/предсказаний, доменные исключения.
- **Infrastructure‑слой (`infrastructure/*`)** - реализует репозитории поверх Postgres (SQL через SQLAlchemy Core), создает DB engine и фабрику соединений.
- **Runtime‑слой (`runtime/*`)** - загружает модельные артефакты с диска, хранит модели и feature_columns, реализует методы predict по use case.
- **Cross‑cutting (`crosscutting/*`)** - реализует логирование, метрики и трассировку, не содержит бизнес‑логики.
- **Dependencies (`dependencies/container.py`)** - собирает граф зависимостей (engine, репозитории, RuntimeManager, сервисы) и предоставляет фабрики для FastAPI `Depends`.
- **Model registry (`domain/infrastructure modelregistry`)** - читает `serving.model_registry`, отдает активную версию модели по имени.
- **Model name resolver (`domain/runtime`)** - сопоставляет use case (например, `churn`) с техническим `model_name` в registry.



## Путь клиентского запроса

```mermaid
flowchart LR
    Backend -->|HTTP JSON /ml/churn/predict| MLAPI[apps/ml_api HTTP endpoint]

    MLAPI -->|десериализация, валидация| APILayer[API слой]
    APILayer -->|создание сервиса через Depends| AppLayer[Application сервис use case]

    AppLayer -->|чтение фич| FeatRepo[Feature репозиторий]
    FeatRepo -->|SQL к mart или feature| Postgres[(PostgreSQL)]
    FeatRepo -->|DTO фич| AppLayer

    AppLayer -->|use case → model_name| NameResolver[Model name resolver]
    NameResolver -->|model_name| ModelRegistry[Model registry репозиторий]
    ModelRegistry -->|SQL к serving.model_registry| Postgres
    ModelRegistry -->|ModelVersionInfo с artifact_path и версией| AppLayer

    AppLayer -->|features и model_name| Runtime[RuntimeManager]
    Runtime -->|raw prediction scores и labels| AppLayer

    AppLayer -->|маппинг в payload DTO| APILayer
    APILayer -->|формирование StubPredictionResponse| Backend

    FeatRepo -->|нет фич| AppLayer
    AppLayer -->|FeaturesNotFoundError| APILayer
    APILayer -->|HTTP 404 с errorCode| Backend

    ModelRegistry -->|нет активной модели| AppLayer
    AppLayer -->|NoActiveModelError| APILayer
    APILayer -->|HTTP 503 с errorCode| Backend
```
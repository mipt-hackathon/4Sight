SHELL := /bin/bash

ENV_FILE := .env
COMPOSE := docker compose --env-file $(ENV_FILE)

.PHONY: ensure-env bootstrap up down logs migrate current backend-shell ml-shell db-shell psql etl marts features train score pipeline test lint format reset-db

ensure-env:
	cp -n .env.example $(ENV_FILE) 2>/dev/null || true

bootstrap: ensure-env
	$(COMPOSE) up -d postgres redis
	$(MAKE) migrate

up: ensure-env
	$(COMPOSE) up --build -d postgres redis backend ml-api frontend superset pgadmin

down:
	$(COMPOSE) down

logs: ensure-env
	$(COMPOSE) logs -f --tail=200

migrate: ensure-env
	$(COMPOSE) run --rm backend alembic upgrade head

current: ensure-env
	$(COMPOSE) run --rm backend alembic current

backend-shell: ensure-env
	$(COMPOSE) run --rm backend bash

ml-shell: ensure-env
	$(COMPOSE) run --rm ml-api bash

db-shell: ensure-env
	$(COMPOSE) exec postgres sh

psql: ensure-env
	$(COMPOSE) exec postgres sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

etl: ensure-env
	$(COMPOSE) run --rm etl

marts: ensure-env
	$(COMPOSE) run --rm marts-builder

features: ensure-env
	$(COMPOSE) run --rm feature-builder

train: ensure-env
	$(COMPOSE) run --rm train

score: ensure-env
	$(COMPOSE) run --rm batch-scoring

pipeline:
	$(MAKE) etl
	$(MAKE) marts
	$(MAKE) features
	$(MAKE) train
	$(MAKE) score

test:
	PYTHONPATH="apps/backend:apps/ml_api:libs/common/src:jobs/etl/src:jobs/marts_builder/src:jobs/feature_builder/src:jobs/train/src:jobs/batch_scoring/src" pytest

lint:
	ruff check .

format:
	ruff format .

reset-db:
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres redis
	$(MAKE) migrate

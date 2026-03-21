SHELL := /bin/bash

COMPOSE := docker compose --env-file .env

.PHONY: up down logs etl marts features train score pipeline test lint format reset-db

up:
	cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up --build -d postgres redis backend ml-api frontend superset pgadmin

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

etl:
	$(COMPOSE) run --rm etl

marts:
	$(COMPOSE) run --rm marts-builder

features:
	$(COMPOSE) run --rm feature-builder

train:
	$(COMPOSE) run --rm train

score:
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

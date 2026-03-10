.PHONY: up down logs build ps shell seed status test lint

up:
	docker compose up -d $(if $(s),$(s))

down:
	docker compose down

logs:
	docker compose logs -f $(s)

build:
	docker compose build $(s)

ps:
	docker compose ps

shell:
	docker compose exec $(s) /bin/sh

db-migrate:
	cd apps/backend && alembic upgrade head

db-rollback:
	cd apps/backend && alembic downgrade -1

db-seed:
	python scripts/seed_agents.py --direct

install:
	pip install -r apps/backend/requirements.txt

lint:
	ruff check apps/ packages/ scripts/

fmt:
	ruff format apps/ packages/ scripts/

test:
	pytest tests/ -v

monitor-seed:
	curl -X POST http://localhost:8000/monitor/seed

status:
	curl -s http://localhost:8000/status

health-sync:
	curl -X POST http://localhost:8000/monitor/sync-health

agents-seed:
	curl -X POST http://localhost:8000/agents/seed/notion

TAG ?= latest
REGISTRY ?= ghcr.io/aegalindezarraiz

push:
	docker compose build
	docker tag vs-api-gateway $(REGISTRY)/api-gateway:$(TAG)
	docker tag vs-backend $(REGISTRY)/backend:$(TAG)
	docker push $(REGISTRY)/api-gateway:$(TAG)
	docker push $(REGISTRY)/backend:$(TAG)

help:
	@echo "AI Venture Studio OS"
	@echo "  make up            Start all services"
	@echo "  make up s=backend  Start specific service"
	@echo "  make down          Stop all"
	@echo "  make logs s=api-gateway"
	@echo "  make build"
	@echo "  make db-migrate"
	@echo "  make monitor-seed  Populate Notion Monitor"
	@echo "  make status        Platform health"
	@echo "  make lint / test"

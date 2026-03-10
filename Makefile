.PHONY: help up down build logs migrate seed test lint format clean

help:
	@echo ""
	@echo "AI Venture Studio OS — Commands"
	@echo "================================"
	@echo "  make up          Start all services"
	@echo "  make down        Stop all services"
	@echo "  make build       Rebuild all images"
	@echo "  make logs        Tail all logs"
	@echo "  make migrate     Run Alembic migrations"
	@echo "  make seed        Seed demo data"
	@echo "  make test        Run all tests"
	@echo "  make lint        Lint Python + TypeScript"
	@echo "  make format      Format all code"
	@echo "  make smoke       Run smoke tests"
	@echo "  make clean       Remove volumes and containers"
	@echo ""

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

test:
	docker compose exec backend pytest apps/backend/tests -v
	cd apps/frontend && npm test -- --run

lint:
	docker compose exec backend ruff check apps/
	cd apps/frontend && npm run lint

format:
	docker compose exec backend ruff format apps/
	cd apps/frontend && npm run format

smoke:
	bash scripts/smoke_test.sh

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

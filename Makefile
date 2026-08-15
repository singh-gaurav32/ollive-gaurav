.PHONY: help up up-all down logs install migrate test test-db run clean

DATABASE_URL ?= postgresql+asyncpg://ollive:ollive@localhost:5432/ollive

help:
	@echo "Ollive - available targets:"
	@echo "  make up        - Start Postgres only (for running backend/tests locally against uv)"
	@echo "  make up-all    - Build and start the full stack (Postgres + API). Reads GEMINI_API_KEY from .env"
	@echo "  make down      - Stop all containers"
	@echo "  make logs      - Tail logs from all containers"
	@echo "  make install   - Install backend dependencies (uv sync)"
	@echo "  make migrate   - Run Alembic migrations against local Postgres"
	@echo "  make test      - Run the backend test suite (real-Postgres integration tests skipped)"
	@echo "  make test-db   - Run the backend test suite including real-Postgres integration tests"
	@echo "  make run       - Run the API locally with auto-reload (outside Docker)"
	@echo "  make clean     - Stop containers AND remove the Postgres data volume (destructive - local dev data only)"

up:
	docker-compose up -d postgres

up-all:
	docker-compose up -d --build

down:
	docker-compose down

logs:
	docker-compose logs -f

install:
	cd backend && uv sync

migrate:
	cd backend && DATABASE_URL=$(DATABASE_URL) uv run alembic upgrade head

test:
	cd backend && uv run pytest -v

test-db:
	cd backend && RUN_DB_TESTS=1 DATABASE_URL=$(DATABASE_URL) uv run pytest tests/db/test_sqlalchemy_repositories.py -v

run:
	cd backend && DATABASE_URL=$(DATABASE_URL) uv run uvicorn main:app --reload --app-dir src

clean:
	docker-compose down -v

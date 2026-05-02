.PHONY: dev worker lint format format-check typecheck check migrate upgrade downgrade \
        test test-unit test-integration test-cov clean install seed-init \
        export-spec generate-sdk help

# Default target - show help
.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (including dev)
	cd backend && uv sync --extra dev

dev: ## Start the development server
	bash dev/start-backend

worker: ## Start the Celery worker
	bash dev/start-worker

lint: ## Run ruff linter
	cd backend && uv run ruff check app/ tests/

format: ## Auto-format code and sort imports
	cd backend && uv run ruff format app/ tests/
	cd backend && uv run ruff check --select I --fix app/ tests/

format-check: ## Check formatting without writing changes
	cd backend && uv run ruff format --check app/ tests/
	cd backend && uv run ruff check --select I app/ tests/

typecheck: ## Run mypy type checker
	cd backend && uv run mypy app/

check: lint format-check typecheck ## Run all checks (lint, format, typecheck)
	@echo "All checks passed."

migrate: ## Generate a new Alembic migration (msg=<description>)
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

upgrade: ## Apply all pending migrations
	cd backend && uv run alembic upgrade head

downgrade: ## Roll back the last migration
	cd backend && uv run alembic downgrade -1

test: ## Run all tests
	cd backend && uv run pytest

test-unit: ## Run unit tests only
	cd backend && uv run pytest tests/unit/ -m unit

test-integration: ## Run integration tests only
	cd backend && uv run pytest tests/integration/ -m integration

test-cov: ## Run tests with coverage report
	cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-report=html

clean: ## Remove caches and build artifacts
	find backend/ -type d -name __pycache__ -exec rm -rf {} +
	find backend/ -type d -name .pytest_cache -exec rm -rf {} +
	find backend/ -type d -name .mypy_cache -exec rm -rf {} +
	find backend/ -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf backend/htmlcov/ backend/.coverage

seed-init: ## Seed with initial data
	cd backend && uv run python -m app.infrastructure.db.seed

# ── SDK generation ──────────────────────────────────────────────────────────
SDK_DIR   := sdk
SPEC_FILE := $(SDK_DIR)/openapi.json
GEN_IMAGE := openapitools/openapi-generator-cli:v7.10.0

export-spec: ## Export OpenAPI spec from FastAPI app (no server required)
	cd backend && uv run python scripts/export_openapi.py --output ../$(SPEC_FILE)

generate-sdk: export-spec ## Generate TypeScript SDK from OpenAPI spec
	docker run --rm \
	  -v "$(PWD)/$(SDK_DIR):/sdk" \
	  $(GEN_IMAGE) generate \
	  -i /sdk/openapi.json \
	  -c /sdk/openapitools.yaml \
	  -o /sdk/javascript-client
	@echo "SDK generated at sdk/javascript-client"


SHELL        := /bin/bash
MAKEFLAGS    += --no-print-directory

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
DOCKER_DIR   := docker
SDK_DIR      := sdk
SPEC_FILE    := $(SDK_DIR)/openapi.json
GEN_IMAGE    := openapitools/openapi-generator-cli:v7.10.0

UV           := cd $(BACKEND_DIR) && uv run
PNPM         := cd $(FRONTEND_DIR) && pnpm

.DEFAULT_GOAL := help

# ── Targets ──────────────────────────────────────────────────────────────────

.PHONY: help \
        install be-install fe-install \
        be-dev fe-dev worker \
        be-lint be-format be-format-check be-typecheck be-check \
        fe-lint fe-format fe-format-check fe-check \
        lint format format-check check \
        test test-unit test-integration test-cov \
        migrate upgrade downgrade seed-init \
        fe-build fe-preview \
        infra-up infra-down infra-logs infra-ps \
        export-spec generate-sdk \
        api-test \
        clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1mUsage:\033[0m\n  make \033[36m<target>\033[0m\n"} \
	     /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } \
	     /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' \
	     $(MAKEFILE_LIST)

# ─────────────────────────────────────────────────────────────────────────────
##@ Install
# ─────────────────────────────────────────────────────────────────────────────

install: be-install fe-install ## Install all dependencies (backend + frontend)

be-install: ## Install backend dependencies (uv sync --extra dev)
	cd $(BACKEND_DIR) && uv sync --extra dev

fe-install: ## Install frontend dependencies (pnpm install)
	$(PNPM) install

# ─────────────────────────────────────────────────────────────────────────────
##@ Development
# ─────────────────────────────────────────────────────────────────────────────

be-dev: ## Start the backend dev server on :8000 (runs migrations first)
	bash dev/start-backend

fe-dev: ## Start the frontend dev server on :5173 (Vite)
	bash dev/start-frontend

worker: ## Start the Celery worker  [QUEUES=  CONCURRENCY=  POOL=  LOGLEVEL=]
	bash dev/start-worker \
	  $(if $(QUEUES),--queues $(QUEUES)) \
	  $(if $(CONCURRENCY),--concurrency $(CONCURRENCY)) \
	  $(if $(POOL),--pool $(POOL)) \
	  $(if $(LOGLEVEL),--loglevel $(LOGLEVEL))

# ─────────────────────────────────────────────────────────────────────────────
##@ Backend quality
# ─────────────────────────────────────────────────────────────────────────────

be-lint: ## Lint backend (ruff)
	$(UV) ruff check app/ tests/

be-format: ## Auto-format backend code (ruff format + import sort)
	$(UV) ruff format app/ tests/
	$(UV) ruff check --select I --fix app/ tests/

be-format-check: ## Check backend formatting without writing changes
	$(UV) ruff format --check app/ tests/
	$(UV) ruff check --select I app/ tests/

be-typecheck: ## Type-check backend (mypy)
	$(UV) mypy app/

be-check: be-lint be-format-check be-typecheck ## Run all backend checks
	@echo "All backend checks passed."

# ─────────────────────────────────────────────────────────────────────────────
##@ Frontend quality
# ─────────────────────────────────────────────────────────────────────────────

fe-lint: ## Lint frontend (ESLint)
	$(PNPM) lint

fe-format: ## Auto-format frontend code (ESLint fix + Prettier)
	$(PNPM) fix-all-files
	$(PNPM) format-all-files

fe-format-check: ## Check frontend formatting without writing changes (Prettier)
	$(PNPM) exec prettier --check .

fe-check: fe-lint fe-format-check ## Run all frontend checks

# ─────────────────────────────────────────────────────────────────────────────
##@ Quality (all)
# ─────────────────────────────────────────────────────────────────────────────

lint: be-lint fe-lint ## Lint backend and frontend

format: be-format fe-format ## Auto-format backend and frontend

format-check: be-format-check fe-format-check ## Check formatting (backend + frontend)

check: be-check fe-check ## Run all checks (backend + frontend)

# ─────────────────────────────────────────────────────────────────────────────
##@ Testing
# ─────────────────────────────────────────────────────────────────────────────

test: ## Run all tests
	$(UV) pytest

test-unit: ## Run unit tests only
	$(UV) pytest tests/unit/ -m unit

test-integration: ## Run integration tests only
	$(UV) pytest tests/integration/ -m integration

test-cov: ## Run tests with coverage report (HTML + terminal)
	$(UV) pytest --cov=app --cov-report=term-missing --cov-report=html

# ─────────────────────────────────────────────────────────────────────────────
##@ Database
# ─────────────────────────────────────────────────────────────────────────────

migrate: ## Generate Alembic migration  [msg=<description>]
	cd $(BACKEND_DIR) && uv run alembic revision --autogenerate -m "$(msg)"

upgrade: ## Apply all pending migrations
	cd $(BACKEND_DIR) && uv run alembic upgrade head

downgrade: ## Roll back the last migration
	cd $(BACKEND_DIR) && uv run alembic downgrade -1

seed-init: ## Seed the database with initial data
	$(UV) python -m app.infrastructure.db.seed

# ─────────────────────────────────────────────────────────────────────────────
##@ Build
# ─────────────────────────────────────────────────────────────────────────────

fe-build: ## Build frontend for production (Vite)
	$(PNPM) build

fe-preview: ## Serve the production frontend build locally
	$(PNPM) preview

# ─────────────────────────────────────────────────────────────────────────────
##@ Infrastructure
# ─────────────────────────────────────────────────────────────────────────────

infra-up: ## Start all Docker services (postgres, redis, minio, mailpit, flower)
	docker compose -f $(DOCKER_DIR)/docker-compose.yml up -d

infra-down: ## Stop and remove Docker services
	docker compose -f $(DOCKER_DIR)/docker-compose.yml down

infra-logs: ## Follow Docker logs  [SERVICE=<name> for a specific service]
	docker compose -f $(DOCKER_DIR)/docker-compose.yml logs -f $(SERVICE)

infra-ps: ## Show status of all Docker services
	docker compose -f $(DOCKER_DIR)/docker-compose.yml ps

# ─────────────────────────────────────────────────────────────────────────────
##@ SDK
# ─────────────────────────────────────────────────────────────────────────────

export-spec: ## Export OpenAPI spec from FastAPI app to sdk/openapi.json
	cd $(BACKEND_DIR) && uv run python scripts/export_openapi.py --output ../$(SPEC_FILE)

generate-sdk: export-spec ## Generate TypeScript SDK from OpenAPI spec
	docker run --rm \
	  -v "$(PWD)/$(SDK_DIR):/sdk" \
	  $(GEN_IMAGE) generate \
	  -i /sdk/openapi.json \
	  -c /sdk/openapitools.yaml \
	  -o /sdk/javascript-client
	@echo "SDK generated at $(SDK_DIR)/javascript-client"

# ─────────────────────────────────────────────────────────────────────────────
##@ API Testing
# ─────────────────────────────────────────────────────────────────────────────

api-test: ## Run Bruno API tests against the local environment  [ENV=local]
	cd bruno && pnpm exec bru run --env $(or $(ENV),local)

# ─────────────────────────────────────────────────────────────────────────────
##@ Utilities
# ─────────────────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches (backend + frontend)
	find $(BACKEND_DIR)/ -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -exec rm -rf {} +
	rm -rf $(BACKEND_DIR)/htmlcov/ $(BACKEND_DIR)/.coverage
	$(PNPM) clean

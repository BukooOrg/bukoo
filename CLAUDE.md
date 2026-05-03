# CLAUDE.md — Bukoo Monorepo

This is the root guidance file. Read it first for orientation, then read the
subdirectory-specific CLAUDE.md for the area you are working in:

- **Backend (FastAPI/Python)** → `backend/CLAUDE.md`
- **Frontend (React/Vite)** → `frontend/CLAUDE.md`

## What Is Bukoo

Premium editorial bookstore ecommerce platform. The backend is a FastAPI Clean
Architecture API. The frontend is a React 19 + Vite SPA. They communicate
through a Vite dev proxy (`/api` → `http://localhost:8000`) and share types via
an auto-generated TypeScript SDK at `sdk/javascript-client` (workspace package
`@bukoo/api-client`).

## Monorepo Layout

```
bukoo/
├── backend/          ← FastAPI Python backend (Python 3.12, uv)
├── frontend/         ← React 19 + Vite SPA (pnpm)
├── sdk/
│   ├── javascript-client/   ← @bukoo/api-client — AUTO-GENERATED, never edit by hand
│   └── openapi.json         ← exported OpenAPI spec (source of truth for SDK)
├── docker/           ← docker-compose.yml + service env templates
├── bruno/            ← Bruno API test collection (auth + health tests)
├── dev/              ← dev launcher scripts (start-backend, start-frontend, start-worker)
├── Makefile          ← ALL make commands live here (run from repo root)
├── pnpm-workspace.yaml  ← pnpm workspace (frontend + sdk/javascript-client)
└── .pre-commit-config.yaml
```

**Ignore:** `backend_legacy/` and `legacy/` are deprecated. Do not modify them.

## Context Artifacts

Detailed reference documents for Claude are in `.claude/context/`:

| File                                      | When to read                                                                                                            |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `.claude/context/project-context.md`      | For orientation: what features exist, who uses them, what is out of scope, implementation status                        |
| `.claude/context/architecture.md`         | Before implementing features that span multiple layers; understanding request lifecycle, session handling, or auth flow |
| `.claude/context/domain-model.md`         | Before adding new entities or use cases; understanding entity relationships and invariants                              |
| `.claude/context/api-endpoint-catalog.md` | Before implementing any route; the authoritative list of all 86 endpoints grouped by API set, with access levels        |

## All Make Targets (run from repo root)

### Install

```bash
make install          # backend + frontend (both)
make be-install       # uv sync --extra dev (backend only)
make fe-install       # pnpm install (frontend only)
```

### Development

```bash
make be-dev           # backend on :8000 (runs alembic upgrade head first)
make fe-dev           # frontend on :5173
make worker           # Celery worker  [QUEUES= CONCURRENCY= POOL= LOGLEVEL=]
```

### Quality checks

```bash
make be-check         # ruff lint + format-check + mypy (backend) — run before committing
make fe-check         # ESLint + Prettier check (frontend) — run before committing
make check            # all checks (backend + frontend)

make be-lint          # ruff check only
make be-format        # ruff format + import sort (auto-fix)
make be-format-check  # ruff format check (no writes)
make be-typecheck     # mypy strict

make fe-lint          # ESLint only
make fe-format        # ESLint fix + Prettier (auto-fix)
make fe-format-check  # Prettier check (no writes)
```

### Testing (backend only — no frontend tests)

```bash
make test             # all pytest tests
make test-unit        # pytest tests/unit/ -m unit
make test-integration # pytest tests/integration/ -m integration
make test-cov         # coverage report (HTML + terminal, output: backend/htmlcov/)
```

### Database

```bash
make migrate msg="add orders table"  # alembic autogenerate — review the generated file
make upgrade                         # alembic upgrade head
make downgrade                       # alembic downgrade -1
make seed-init                       # seed initial data
```

### Infrastructure

```bash
make infra-up         # docker compose up -d (all services)
make infra-down       # docker compose down
make infra-logs       # follow logs  [SERVICE=<name> for one service]
make infra-ps         # show service status
```

### SDK

```bash
make export-spec      # export OpenAPI JSON → sdk/openapi.json
make generate-sdk     # export-spec + regenerate TypeScript client (requires Docker)
```

### API testing

```bash
make api-test         # Bruno tests against local environment  [ENV=local]
```

### Build / clean

```bash
make fe-build         # Vite production build
make fe-preview       # serve production build locally
make clean            # remove all build artifacts and caches
```

## Infrastructure Services

Start with `make infra-up`. All services are required before running the backend or worker.

| Service    | Port(s)     | Purpose                        |
| ---------- | ----------- | ------------------------------ |
| PostgreSQL | 5432        | Primary database               |
| pgAdmin    | 5050        | Database UI                    |
| Mailpit    | 1025 / 8025 | SMTP trap (dev email testing)  |
| MinIO      | 9000 / 9001 | Object storage (local S3)      |
| Redis      | 6379        | Celery broker + result backend |
| Flower     | 5555        | Celery task monitoring         |

Docker env is loaded from `docker/.env.dev` (copy from `docker/.env.dev.example`).

## SDK Regeneration Workflow

`sdk/javascript-client` is always generated — never hand-edited. When backend
API schemas change or new routes are added:

1. `make export-spec` — exports `sdk/openapi.json`
2. `make generate-sdk` — regenerates `sdk/javascript-client/` via Docker
3. Frontend imports from `@bukoo/api-client` (workspace `*` reference in `frontend/package.json`)

## Commit Message Rules

Format: `type(scope): subject` — scope is optional.

Allowed types: `feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore` |
`build` | `ci` | `perf` | `revert` | `security` | `translation`

Rules (enforced by gitlint + pre-commit):

- Lowercase type and scope
- No trailing punctuation on subject (`?:!.,;` are forbidden)
- Subject minimum 10 characters, maximum 100 characters
- Body must start with a blank line (if present)
- Body lines maximum 100 characters

Examples:

```
feat(auth): add google oauth login endpoint
fix(cart): correct quantity update on duplicate items
refactor(domain): extract isbn validation into value object
```

## Pre-commit Hooks

Configured in `.pre-commit-config.yaml`. Run automatically on `git commit`:

- **ruff** — lint + format (backend Python files in `backend/`)
- **eslint** — lint + Prettier fix (frontend JS/JSX files)
- **mypy** — type-check backend (`uv run mypy app/`)
- **gitlint** — commit message format check

To run all hooks manually: `pre-commit run --all-files`

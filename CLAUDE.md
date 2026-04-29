# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All `make` commands run from the **project root** (the Makefile lives there):

```bash
make help                    # list all available targets
make install                 # uv sync --extra dev
make dev                     # uvicorn main:app --reload --host 0.0.0.0 --port 8000
make lint                    # ruff check app/ tests/
make format                  # ruff format + ruff check --select I --fix (import sorting)
make typecheck               # mypy app/
make import-lint             # lint-imports (Clean Architecture boundary check)
make check                   # lint + format-check + typecheck + import-lint
make test                    # all tests
make test-unit               # pytest tests/unit/ -m unit
make test-cov                # pytest with coverage report
make migrate msg="description"  # alembic autogenerate revision
make upgrade                 # alembic upgrade head
make downgrade               # alembic downgrade -1
```

Infrastructure (Docker):

```bash
docker compose up -d   # start postgres, pgadmin, mailpit, minio
```

## Architecture

The backend follows **Clean Architecture** with four strictly ordered layers. Dependencies flow inward only — inner layers never import from outer ones.

```
domain/          ← entities, repository interfaces (Protocols), domain services, exceptions
application/     ← use cases, DTOs, application-layer interfaces (ports)
infrastructure/  ← SQLAlchemy repos, JWT, bcrypt, Razorpay, MinIO/S3, SMTP
presentation/    ← FastAPI routers, Pydantic schemas, FastAPI Depends()
```

### Key design patterns

**Composition root** — `app/presentation/dependencies/deps.py` is the only file that imports from both `application/` and `infrastructure/` simultaneously. All `Depends()` providers live there. Do not wire infrastructure into use cases directly in route handlers.

**Repository interfaces** — defined as `typing.Protocol` in `app/domain/repositories/`. Use cases depend on these protocols, never on `*RepositoryImpl`. SQLAlchemy implementations live in `app/infrastructure/db/repositories/`.

**Mappers** — ORM models (`app/infrastructure/db/models/`) never enter the domain layer. `*Mapper` classes in `app/infrastructure/db/mappers/` translate between ORM models and domain entities.

**Strategy pattern** — `LoginUseCase` accepts an `IAuthStrategy` so credential login and Google OAuth share the same use case. The correct strategy is injected in `deps.py`.

**Factory pattern** — `PaymentServiceFactory` (in `app/infrastructure/payment/factory.py`) self-registers providers via decorator. `app/infrastructure/payment/__init__.py` must be imported to trigger registration; `deps.py` does this.

### Domain exceptions

All domain exceptions inherit from `DomainException` in `app/domain/exceptions.py`. The FastAPI app in `main.py` maps these to HTTP status codes via `@app.exception_handler`. Never raise `HTTPException` from inside domain or application layers.

### Database

- Async SQLAlchemy with `asyncpg` driver
- `DATABASE_URL` must use `postgresql+asyncpg://` scheme
- Session lifecycle managed in `app/infrastructure/db/session.py` (singleton engine + per-request session via `get_db_session`)
- Alembic migrations live in `backend/migrations/`; all ORM models are imported in `migrations/env.py` for autogenerate to work

### Testing approach

Unit tests use **fake in-memory repositories** (defined in `tests/conftest.py`) — no mocking framework, no database. This lets use cases be tested in isolation. Integration tests (not yet written) hit a real DB.

## Known deviations from scaffold

- `bcrypt` pinned to `<4.0.0` — bcrypt 5.x broke `passlib` compatibility
- `TCH`, `UP042`, `N818` ruff rules are suppressed (TYPE_CHECKING blocks break FastAPI Depends; `str+Enum` and `DomainException` naming are intentional scaffold choices)
- ISBN test uses `"1234567890123"` (not `"0000000000000"` — all-zeros passes checksum)

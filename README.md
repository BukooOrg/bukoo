# Bukoo

A premium editorial-minimalism bookstore ecommerce platform.

**Stack:** FastAPI · Python 3.12 · SQLAlchemy (async) · PostgreSQL · Redis · Celery · MinIO · React 19 · Vite · Tailwind CSS

---

## Prerequisites

### OS

Ubuntu 22.04+ or WSL2 on Windows is required. macOS may work but is untested.

### Required tools

| Tool           | Version | Install                                                                               |
| -------------- | ------- | ------------------------------------------------------------------------------------- |
| Docker Desktop | latest  | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| Docker Compose | v2+     | bundled with Docker Desktop                                                           |
| Make           | any     | `sudo apt install build-essential`                                                    |
| Python         | 3.12+   | managed by `uv` — no manual install needed                                            |
| uv             | latest  | `curl -LsSf https://astral.sh/uv/install.sh \| sh`                                    |
| nvm            | latest  | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/HEAD/install.sh \| bash`       |
| Node.js        | 22      | via nvm — see setup below                                                             |
| pnpm           | 10.33+  | via corepack — see setup below                                                        |

> **Note:** `uv` replaces pip/poetry for the backend. It manages the Python version and virtual environment automatically — you do not need to create a venv manually.

### Node.js and pnpm setup

The project pins Node.js to v22 via `.nvmrc` and pnpm via the `packageManager` field in `package.json`. Use nvm and corepack to stay in sync automatically — **do not install Node.js or pnpm via any other method**.

```bash
# 1. Install nvm (restart your terminal after this)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/HEAD/install.sh | bash

# 2. Install the project's Node version (reads .nvmrc automatically)
nvm install

# 3. Enable corepack (ships with Node.js — manages pnpm version)
corepack enable

# 4. Activate the correct pnpm version declared in package.json
corepack install
```

After this, `node --version` should print `v22.x.x` and `pnpm --version` should print `10.33.x`.

> **Tip:** Add `nvm use` (or `nvm use --silent`) to your shell profile or use a tool like [direnv](https://direnv.net/) to switch Node versions automatically when entering this directory.

### Recommended

- **[pgweb](https://github.com/sosedoff/pgweb)** — lightweight browser-based PostgreSQL client. Simpler than pgAdmin for quick queries:
  ```bash
  # Linux / WSL2
  curl -s https://api.github.com/repos/sosedoff/pgweb/releases/latest \
    | grep "browser_download_url.*linux_amd64" \
    | cut -d '"' -f 4 | wget -qi - && \
    unzip pgweb_linux_amd64.zip && sudo mv pgweb_linux_amd64 /usr/local/bin/pgweb
  ```
  Then run `pgweb --host localhost --port 5432 --user postgres --db bukoo`.

---

## Recommended VS Code Extensions

| Extension                                   | Purpose                                        |
| ------------------------------------------- | ---------------------------------------------- |
| `ms-python.python`                          | Python language support                        |
| `ms-python.vscode-pylance`                  | Python IntelliSense                            |
| `charliermarsh.ruff`                        | Linting and formatting (replaces flake8/black) |
| `ms-python.mypy-type-checker`               | Type checking                                  |
| `dbaeumer.vscode-eslint`                    | JavaScript/JSX linting                         |
| `esbenp.prettier-vscode`                    | Frontend code formatting                       |
| `bradlc.vscode-tailwindcss`                 | Tailwind CSS IntelliSense and autocomplete     |
| `ms-azuretools.vscode-docker`               | Docker container and compose management        |
| `usebruno.bruno`                            | Bruno API client (in-editor API testing)       |
| `mtxr.sqltools` + `mtxr.sqltools-driver-pg` | SQL editor with PostgreSQL support             |

---

## First-time Setup

Complete these steps once after cloning the repository.

### 1. Copy environment files

```bash
# Backend
cp backend/.env.example backend/.env

# Docker
cp docker/.env.dev.example docker/.env.dev
```

Open `backend/.env` and set at minimum:

```
SECRET_KEY=<any-random-string>
```

Generate a secure secret key with the command:

```
openssl rand -base64 32
```

Everything else defaults to values that work with the Docker setup out of the box.

### 2. Start Docker infrastructure

```bash
make infra-up
```

This starts: PostgreSQL · pgAdmin · Mailpit · MinIO · Redis · Flower.

Verify all services are healthy:

```bash
make infra-ps
```

### 3. Install dependencies

```bash
make install
```

This runs `uv sync` for the backend and `pnpm install` for the frontend.

### 4. Run database migrations

```bash
make upgrade
```

### 5. Seed initial data

```bash
make seed-init
```

This creates the default admin user (`admin@gmail.com` / `Adm!n123` — configurable in `backend/.env`).

---

## Running the App

Open three terminal windows:

```bash
# Terminal 1 — backend (auto-runs migrations on start)
make be-dev

# Terminal 2 — frontend
make fe-dev

# Terminal 3 — Celery worker (only needed for background tasks)
make worker
```

---

## Dev Service URLs

| Service            | URL                         | Credentials                                     |
| ------------------ | --------------------------- | ----------------------------------------------- |
| Frontend           | http://localhost:5173       | —                                               |
| Backend API        | http://localhost:8000       | —                                               |
| API Docs (Swagger) | http://localhost:8000/docs  | —                                               |
| API Docs (ReDoc)   | http://localhost:8000/redoc | —                                               |
| pgAdmin            | http://localhost:5050       | `postgres@gmail.com` / `postgres` (if prompted) |
| pgweb              | http://localhost:8081       | see pgweb section above                         |
| Mailpit (email)    | http://localhost:8025       | —                                               |
| MinIO Console      | http://localhost:9001       | `minioadmin` / `minioadmin`                     |
| Flower (Celery)    | http://localhost:5555       | —                                               |

---

## Make Commands Reference

Run all commands from the **project root**.

### Pre Install

```bash
sudo chmod -R +x .    # change files permission to be executable
```

### Install

```bash
make install          # install backend + frontend dependencies
make be-install       # backend only (uv sync)
make fe-install       # frontend only (pnpm install)
```

### Post Install

```bash
uv tool install pre-commit    # install pre-commit package
./dev/install-git-hooks       # install git hooks
```

### Development

```bash
make be-dev           # backend dev server on :8000 (runs migrations first)
make fe-dev           # frontend dev server on :5173 (Vite)
make worker           # Celery worker for background tasks
```

### Code Quality

```bash
make check            # run all checks (lint + format-check + typecheck)
make be-check         # backend only
make fe-check         # frontend only

make format           # auto-fix formatting (backend + frontend)
make lint             # lint only (no fixes)
```

### Testing

```bash
make test             # all tests
make test-unit        # unit tests only (in-memory, no DB)
make test-integration # integration tests (requires running DB)
make test-cov         # tests with HTML coverage report
```

### Database

```bash
make upgrade                  # apply all pending migrations
make downgrade                # roll back the last migration
make migrate msg="description" # generate a new Alembic migration
make seed-init                 # seed initial data
```

### Infrastructure

```bash
make infra-up         # start all Docker services
make infra-down       # stop and remove Docker services
make infra-ps         # show service status
make infra-logs       # follow all logs  (SERVICE=postgres for one service)
```

### SDK

```bash
make export-spec      # export OpenAPI spec to sdk/openapi.json
make generate-sdk     # regenerate the TypeScript client from the spec
```

### API Testing

```bash
make api-test         # run Bruno API tests against local environment
```

---

## Environment Variables

### `backend/.env`

Loaded by the FastAPI app at runtime. Copy from `backend/.env.example`.

| Variable            | Default                            | Description                            |
| ------------------- | ---------------------------------- | -------------------------------------- |
| `SECRET_KEY`        | `secret-key`                       | JWT signing secret — **change this**   |
| `DATABASE_URL`      | \_(auto-built from POSTGRES\_\_)\* | Set individually via `POSTGRES_*` vars |
| `POSTGRES_USER`     | `postgres`                         | PostgreSQL username                    |
| `POSTGRES_PASSWORD` | `postgres`                         | PostgreSQL password                    |
| `POSTGRES_DB`       | `bukoo`                            | Database name                          |
| `REDIS_URL`         | `redis://localhost:6379/0`         | Celery broker URL                      |
| `SMTP_HOST`         | `localhost`                        | SMTP server (Mailpit in dev)           |
| `SMTP_PORT`         | `1025`                             | Mailpit SMTP port                      |
| `MINIO_ENDPOINT`    | `localhost:9000`                   | MinIO server address                   |
| `STORAGE_TYPE`      | `minio`                            | `minio` in dev, `s3` in production     |
| `GOOGLE_CLIENT_ID`  | —                                  | Required only if using Google OAuth    |

### `docker/.env.dev`

Loaded by Docker Compose only. Controls container environment variables (DB init, pgAdmin credentials, etc.). The defaults work for local development without changes.

---

## Architecture

The backend follows Clean Architecture with four strictly ordered layers. Dependencies flow inward only — inner layers never import from outer ones.

```
domain/          ← entities, repository interfaces (Protocols), domain services
application/     ← use cases, DTOs
infrastructure/  ← SQLAlchemy repos, JWT, bcrypt, MinIO/S3, SMTP, Celery tasks
presentation/    ← FastAPI routers, Pydantic schemas, FastAPI Depends()
```

The composition root (`app/presentation/dependencies/deps.py`) is the only file that wires `application/` and `infrastructure/` together.

---

## API Testing with Bruno

API test collections live in the `bruno/` directory.

To run all tests against the local environment:

```bash
make api-test
```

To run interactively, open the `bruno/` folder in the [Bruno desktop app](https://www.usebruno.com/) or the VS Code Bruno extension and select the `local` environment.

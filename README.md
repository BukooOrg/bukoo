# Bookstore

A full-stack bookstore application.

## Stack

- **Backend**: FastAPI · Python 3.12 · SQLAlchemy (async) · Alembic · PostgreSQL
- **Frontend**: TBD
- **Infra (dev)**: Docker Compose — PostgreSQL · Mailpit · pgAdmin · MinIO

## Quick Start

### 1. Copy env file

```bash
cp .env.example .env
```

### 2. Start infrastructure

```bash
docker compose up -d
```

### 3. Start backend

```bash
cd backend
make install
make upgrade   # run migrations
make dev
```

### 4. Start frontend

```bash
cd frontend
# instructions TBD once framework is chosen
```

## Service URLs (dev)

| Service  | URL                        |
| -------- | -------------------------- |
| Backend  | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |
| pgAdmin  | http://localhost:5050      |
| Mailpit  | http://localhost:8025      |
| MinIO UI | http://localhost:9001      |

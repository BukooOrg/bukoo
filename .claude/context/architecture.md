# Architecture Reference — Bukoo Backend

Deep-dive reference for the FastAPI Clean Architecture implementation.
Read this when implementing features that span multiple layers, or when you need
to understand request lifecycle, session handling, or auth flow.

For actionable task instructions see `backend/CLAUDE.md`.

---

## Layer Dependency Diagram

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  presentation/  (FastAPI, Pydantic, middlewares, deps.py)   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  application/  (use cases, DTOs, service interfaces) │   │
│  │  ┌─────────────────────────────────────────────────┐ │   │
│  │  │  domain/  (entities, repo protocols, exceptions) │ │   │
│  │  └─────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
┌──────────────────────────────────────────────────────────────┐
│  infrastructure/  (SQLAlchemy, JWT, bcrypt, Celery, MinIO)   │
│  (implements domain repository protocols and app interfaces) │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
External services (PostgreSQL, Redis, MinIO/S3, SMTP, Google OAuth)
```

**Forbidden import directions (checked by mypy + ruff import-lint):**
- `domain/` → any outer layer
- `application/` → `infrastructure/` or `presentation/`
- `infrastructure/` → `presentation/`
- ORM models → `domain/` or `application/`

**`core/`** is a special utility layer (settings, logger, constants) that is
importable from any layer including `domain/`.

---

## Composition Root Deep-Dive

`app/presentation/dependencies/deps.py` is the **single** place that stitches
together `application/` interfaces with `infrastructure/` implementations.

### Why it exists

Without a composition root, route handlers would need to import from both
`application/` and `infrastructure/` — violating layer boundaries and making
testing hard. `deps.py` is the explicit exception where crossing is allowed.

### How to extend it

For every new repository or service add:
1. A provider function that creates the implementation
2. A typed `Annotated` alias for use in route handlers

```python
# deps.py

def get_book_repository(session: DbSession) -> IBookRepository:
    return BookRepositoryImpl(session)

BookRepo = Annotated[IBookRepository, Depends(get_book_repository)]
```

Route handlers receive only `BookRepo`, never `BookRepositoryImpl` directly.
This means tests can inject a fake repository without touching the routes.

### What does NOT go in deps.py

- Business logic (belongs in use cases)
- Database queries (belong in repositories)
- HTTP error handling (belongs in exception handlers)

---

## Full Request Lifecycle

```
Client HTTP request
     │
     ▼
RequestContextMiddleware
  → generates/extracts X-Request-ID
  → attaches logger with request_id context variable
     │
     ▼
ResponseFormatterMiddleware
  → intercepts response after route handler returns
  → wraps JSON body in {success, data, meta} envelope
  → passes non-JSON responses through unchanged
     │
     ▼
CORSMiddleware
  → checks Origin header against CORS_ORIGINS config
     │
     ▼
Route handler (presentation/api/)
  → validates request body via Pydantic schema
  → resolves Depends() — calls provider functions in deps.py
  → instantiates use case with resolved dependencies
  → calls use_case.execute()
     │
     ▼
Use case (application/use_cases/)
  → calls repository methods (domain Protocol interfaces)
  → raises DomainException if a rule is violated
  → calls await self._db_session.commit() after successful mutations
  → returns a DTO or domain entity
     │
     ▼
Repository implementation (infrastructure/db/repositories/)
  → executes SQLAlchemy async queries
  → calls Mapper.to_entity() to convert ORM model → domain entity
  → NEVER calls commit()
     │
     ▼
SQLAlchemy AsyncSession
  → executes SQL via asyncpg on PostgreSQL
     │
     ▼
Response: entity/DTO returned up the stack → Pydantic schema → JSON →
ResponseFormatterMiddleware wraps it → client receives envelope
```

### On exceptions

If the use case raises a `DomainException`:
- `domain_exception_handler` in `app/presentation/http/base_handler.py` catches it
- Looks up the exception type in `EXCEPTION_MAP` (exception_mapper.py)
- Returns a structured error envelope with HTTP status, `ErrorCode`, and message

If Pydantic fails request validation:
- `validation_exception_handler` returns 422 with field-level error details

---

## ORM Model Hierarchy

```
Base (DeclarativeBase + MappedAsDataclass)
  └── DefaultFieldMixin  (abstract=True)
        ├── TimestampMixin  → created_at, updated_at  (both init=False)
        └── UuidV7Mixin     → id (UUIDv7 string, init=False, insert_default=uuid7_str)

SoftDeleteMixin (standalone, add alongside DefaultFieldMixin)
  → deleted_at: datetime | None  (init=False, default=None)
  → is_deleted: bool  (property)
```

Concrete model declaration:
```python
class OrderModel(DefaultFieldMixin, SoftDeleteMixin):
    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship loaded always (selectin):
    items: Mapped[list[OrderItemModel]] = relationship(
        "OrderItemModel", lazy="selectin", init=False
    )
    # Relationship loaded on demand only (noload):
    user: Mapped[UserModel] = relationship(
        "UserModel", lazy="noload", init=False
    )
```

---

## Mapper Contract

Every mapper inherits `BaseMapper[ModelType, EntityType]` in
`app/infrastructure/db/mappers/base_mapper.py`.

```python
class BookMapper(BaseMapper[BookModel, BookEntity]):
    @staticmethod
    def to_entity(model: BookModel) -> BookEntity:
        return BookEntity(
            _id=model.id,
            _title=model.title,
            _isbn=model.isbn,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: BookEntity) -> BookModel:
        return BookModel(
            title=entity.title,
            isbn=entity.isbn,
        )
        # Note: id, created_at, updated_at are handled by DefaultFieldMixin
        # and must be set explicitly after: model.id = entity.id
```

ORM models **never** cross into `domain/` or `application/`. The boundary is
the mapper. Domain entities and application DTOs know nothing about SQLAlchemy.

---

## Session Lifecycle

Defined in `app/infrastructure/db/session.py`.

- A singleton `AsyncEngine` is created once per process from `DATABASE_URL`
- `get_db_session()` is a FastAPI dependency that creates an `AsyncSession` per
  request (via `async with AsyncSession(engine) as session:`)
- The session is injected into route handlers as `DbSession` (see `deps.py`)
- Use cases receive `db_session: AsyncSession` and commit explicitly after mutations
- Session is closed automatically when the request ends (context manager in `get_db_session`)

**Why use cases commit:**
- Single unit-of-work responsibility — the use case decides when the transaction is complete
- Repositories must not commit so that multi-repository operations (within one use case) form a single transaction

`session_scope()` is an async context manager for non-request contexts (e.g. the `_create_system_admin_user` lifespan hook):
```python
async with session_scope() as db_session:
    # create repositories, run use case, session is committed and closed automatically
```

---

## Storage Abstraction

`ObjectStorageConfig.STORAGE_TYPE` (from `.env`: `minio` or `s3`) controls which
implementation is returned by `get_storage_service()` in `deps.py`:

```python
match configs.STORAGE_TYPE:
    case ObjectStorageType.MINIO:
        return MinIOStorage()   # app/infrastructure/storage/minio_storage.py
    case ObjectStorageType.S3:
        return S3Storage()      # app/infrastructure/storage/s3_storage.py
```

Both implement `IStorageService` from `app/application/interfaces/storage_service.py`.
Development uses MinIO (local S3-compatible server at `:9000`). Production uses AWS S3.

---

## Auth Flow

### Credential Login (email + password)

```
POST /api/app/v1/auth/login
  → LoginRequest (email, password)
  → LoginUseCase.execute({"email": ..., "password": ...})
  → CredentialProvider.authenticate(credentials)
      → user_repo.find_by_email(email)
      → hasher.verify(password, user.hashed_password)
      → raises InvalidCredentialsError if mismatch
      → returns UserEntity
  → token_svc.create_access_token(user.id)
  → TokenDTO(access_token=...)
```

### Google OAuth Login

```
POST /api/app/v1/auth/login/google
  → GoogleLoginRequest (code, redirect_uri)
  → LoginUseCase.execute({"code": ..., "redirect_uri": ...})
  → GoogleProvider.authenticate(credentials)
      → exchanges code for Google ID token via httpx
      → finds or creates user + account
      → commits transaction
      → returns UserEntity
  → token_svc.create_access_token(user.id)
  → TokenDTO(access_token=...)
```

**Strategy pattern:** `LoginUseCase` accepts `IAuthStrategy`, so credential and
Google OAuth share the same use case class. The correct strategy is injected via
`CredentialStrategy` or `GoogleStrategy` typed aliases in `deps.py`.

### Token Validation Guard (`CurrentUser`)

```
Bearer token from Authorization header
  → JWTService.decode_token(token)
      → raises TokenExpiredError or InvalidTokenError on failure
  → user_repo.find_by_id(user_id from payload["sub"])
  → raises HTTP 401 if user not found or not active
  → returns UserEntity
```

Note: `get_current_user` in `deps.py` raises `HTTPException` directly (not
`DomainException`) because token errors are presentation-layer concerns.

---

## Celery Configuration

```
broker: Redis (REDIS_URL from .env, e.g. redis://localhost:6379/0)
result_backend: Redis (same URL)

Queue routing:
  - "email.*" task names → "mail" queue
  - all others → "default" queue

Task includes (must list every task module):
  - app.infrastructure.tasks.email_tasks

Worker launch: make worker (QUEUES=mail,default by default)
Monitor: http://localhost:5555 (Flower)
```

To add a new queue, update the `task_routes` in `create_celery()` in
`app/infrastructure/tasks/celery_app.py` and adjust `dev/start-worker`.

---

## OpenAPI Schema Patching

`AppFactory._patch_openapi_response_schemas()` in `app/setup.py` modifies the
FastAPI-generated OpenAPI schema after app creation to show the actual HTTP
response envelope shapes. Without this, the spec would show the raw Pydantic
response models, not the `{success, data, meta}` wrapper.

- 2xx responses: schema replaced with `ResponseWrapper{InnerModel}`
- 4xx/5xx responses: schema replaced with `ErrorResponse`

This is called once during app startup and the result is cached on
`application.openapi_schema`. The TypeScript SDK is generated from this patched
spec, so client types include the envelope.

# backend/CLAUDE.md

Detailed guide for the FastAPI backend. Read `../CLAUDE.md` first for monorepo
commands, infrastructure services, and commit rules.

## Quick Reference

- **Entry point:** `app/main.py` → `AppFactory.create_application()` in `app/setup.py`
- **Run:** `make be-dev` (runs `alembic upgrade head` first via `dev/start-backend`)
- **API base path:** `/api/app/v1/` (e.g. `POST /api/app/v1/auth/register`)
- **API docs:** `http://localhost:8000/docs` (only in non-production environments)
- **Env file:** `backend/.env` (copy from `backend/.env.example`)
- **All make targets** run from the **repo root**, not from `backend/`

## Clean Architecture — Layer Rules

Dependencies flow inward only. Inner layers never import from outer ones.

```
domain/          ← innermost: entities, repository Protocols, domain exceptions
application/     ← use cases, DTOs, service interfaces (ports)
infrastructure/  ← ORM models, repository impls, JWT, bcrypt, Celery, MinIO, SMTP
presentation/    ← FastAPI routers, Pydantic schemas, middlewares, deps.py
core/            ← settings, logger, constants (importable from any layer)
```

**Hard rules — violations break the architecture:**

| Layer             | Must NOT import from                                   |
| ----------------- | ------------------------------------------------------ |
| `domain/`         | `application/`, `infrastructure/`, `presentation/`     |
| `application/`    | `infrastructure/`, `presentation/`                     |
| `infrastructure/` | `presentation/`                                        |
| ORM models        | `domain/` or `application/` (use mappers to translate) |

Use cases depend on repository `ABC` interfaces, never on `*RepositoryImpl`.

## The Composition Root: `deps.py`

`app/presentation/dependencies/deps.py` is the **only** file that imports from
both `application/` and `infrastructure/` simultaneously. All FastAPI
`Depends()` providers live there. When adding a new repository or service,
add its provider function and typed alias to `deps.py` only.

Wiring pattern:

```python
# deps.py — typed dependency alias
def get_book_repository(session: DbSession) -> IBookRepository:
    return BookRepositoryImpl(session)

BookRepo = Annotated[IBookRepository, Depends(get_book_repository)]

# Route handler — never instantiate infrastructure inside the handler
async def create_book(repo: BookRepo, db_session: DbSession) -> BookResponse:
    use_case = CreateBookUseCase(db_session=db_session, book_repo=repo)
    ...
```

## Adding a New Feature — Exact Step Order

Follow this sequence to respect layer dependencies:

1. **Domain entity** (`app/domain/entities/<name>_entity.py`)
   - Pure Python `@dataclass` with private `_field` names and `@property` getters
   - IDs created as `str(uuid7())` from `uuid_extension` (not `uuid.uuid4()`)
   - Business methods update `_updated_at = datetime.now(UTC)` on mutation
   - No imports from `infrastructure/` or `application/`

2. **Domain exceptions** (`app/domain/exceptions/<group>.py` + export in `__init__.py`)
   - Inherit from `DomainException` in `app/domain/exceptions/base.py`
   - HTTP-agnostic — no status codes, no FastAPI imports

3. **Repository interface** (`app/domain/repositories/<name>_repository.py`)
   - `ABC` with `@abstractmethod` methods
   - Method signatures use domain entities, never ORM models

4. **DTOs / service interfaces** (`app/application/dtos/`, `app/application/interfaces/`)
   - Frozen `@dataclass` for commands and result types
   - Service interfaces as `ABC` classes

5. **Use case** (`app/application/use_cases/<group>/<action>.py`)
   - Inherits `BaseUseCase` (requires `db_session: AsyncSession` in `__init__`)
   - Depends only on interfaces, never on implementations
   - Call `await self._db_session.commit()` explicitly after mutations
   - Raise domain exceptions, never `HTTPException`

6. **ORM model** (`app/infrastructure/db/models/<name>_model.py`)
   - Inherit `DefaultFieldMixin` (provides UUIDv7 `id`, `created_at`, `updated_at`)
   - Add `SoftDeleteMixin` for soft-deletable tables (`deleted_at`)
   - Default relationship loading: `lazy="noload"`; use `lazy="selectin"` only for always-needed relations
   - **CRITICAL:** import the new model in `backend/migrations/env.py` — Alembic autogenerate only detects imported models

7. **Mapper** (`app/infrastructure/db/mappers/<name>_mapper.py`)
   - Static `to_entity(model)` and `to_model(entity)` methods
   - Inherit `BaseMapper[ModelType, EntityType]`
   - `to_entity` maps all ORM fields to entity private fields (`_field=model.field`)

8. **Repository implementation** (`app/infrastructure/db/repositories/<name>_repository_impl.py`)
   - Implements the domain repository interface
   - `@override` on each method
   - Receives `AsyncSession` in `__init__`
   - Queries always filter `Model.deleted_at.is_(None)` unless fetching deleted records
   - Use `session.merge(model)` for upserts; **never call `commit()`** — only use cases commit

9. **Exception mapping** (`app/presentation/http/exception_mapper.py`)
   - Add new exceptions to `EXCEPTION_MAP` with their HTTP status code and `ErrorCode`

10. **Error codes** (`app/application/errors/error_codes.py`)
    - Add a new `ErrorCode` enum member

11. **Pydantic schemas** (`app/presentation/schemas/<feature>_schema.py`)
    - Request and response models
    - Use `ResponseWrapper[YourResponseSchema]` as `response_model` for success responses

12. **Route handler** (`app/presentation/api/app_api/v1/<feature>_routes.py`)
    - `APIRouter(prefix="/<feature>", tags=["<feature>"])`
    - Register in `app/presentation/api/app_api/v1/__init__.py`

13. **Wire in `deps.py`** — add repository/service provider functions and typed aliases

14. **Generate migration** — `make migrate msg="add <entity> table"` then review the file in `backend/migrations/versions/`

## Domain Entity Pattern

```python
@dataclass
class BookEntity:
    _id: str
    _title: str
    _isbn: str | None
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    def update_title(self, title: str) -> None:
        self._title = title
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
```

Relationships that are always loaded: declare with `_relation: EntityType | None = None`
and pass `lazy="selectin"` on the ORM side.

## ORM Model Pattern

`DefaultFieldMixin` provides: `id` (UUIDv7 string, `init=False`), `created_at`
(`init=False`), `updated_at` (`init=False`). `SoftDeleteMixin` adds `deleted_at`.

```python
class BookModel(DefaultFieldMixin, SoftDeleteMixin):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher_id: Mapped[str | None] = mapped_column(
        ForeignKey("publishers.id"), nullable=True
    )
    publisher: Mapped[PublisherModel | None] = relationship(
        "PublisherModel", lazy="selectin", init=False
    )
```

## Repository Implementation Pattern

```python
class BookRepositoryImpl(IBookRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_id(self, book_id: str) -> BookEntity | None:
        stmt = (
            select(BookModel)
            .where(BookModel.id == book_id)
            .where(BookModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return BookMapper.to_entity(model) if model else None

    @override
    async def save(self, book: BookEntity) -> None:
        model = BookMapper.to_model(book)
        model.id = book.id
        model.deleted_at = book.deleted_at
        await self._session.merge(model)
```

Never call `session.commit()` in a repository. The calling use case commits.

## Domain Exceptions

All inherit from `DomainException` in `app/domain/exceptions/base.py`.
Exported from `app/domain/exceptions/__init__.py`.

| Group   | Exceptions                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| auth    | `InvalidCredentialsError`, `UserAlreadyExistsError`, `UserNotFoundError`, `TokenExpiredError`, `InvalidTokenError`, `UserNotVerifiedError` |
| book    | `BookNotFoundError`, `BookAlreadyExistsError`, `InvalidISBNError`                                                                          |
| order   | `OrderNotFoundError`, `OrderAlreadyPaidError`, `OutOfStockError`, `EmptyOrderError`                                                        |
| payment | `PaymentCreationError`, `PaymentVerificationError`                                                                                         |
| storage | `StorageUploadError`, `StorageNotFoundError`                                                                                               |

To add a new domain exception:

1. Create it in the appropriate group file inheriting from `DomainException`
2. Export from `app/domain/exceptions/__init__.py`
3. Add an `ErrorCode` entry in `app/application/errors/error_codes.py`
4. Add to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`

## API Response Envelope

`ResponseFormatterMiddleware` wraps **all** successful JSON responses automatically.
`domain_exception_handler` wraps error responses. Never wrap responses manually.

Success (2xx):

```json
{
  "success": true,
  "data": { "...your response model..." },
  "meta": { "requestId": "...", "timestamp": "..." }
}
```

Error (4xx/5xx):

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": null
  },
  "meta": { "requestId": "...", "timestamp": "..." }
}
```

Paths that bypass the envelope: `/health`, `/docs`, `/redoc`, `/openapi.json`.

## Current API Routes

All routes are prefixed `/api/app/v1/`:

| Method | Path                            | Description        |
| ------ | ------------------------------- | ------------------ |
| POST   | `/api/app/v1/auth/register`     | Register new user  |
| POST   | `/api/app/v1/auth/login`        | Credential login   |
| POST   | `/api/app/v1/auth/login/google` | Google OAuth login |
| GET    | `/api/app/v1/health`            | Health check       |

To add new routes for the same version: create `<feature>_routes.py` under
`app/presentation/api/app_api/v1/` and register in the `v1/__init__.py`.

## Configuration

All settings come from `backend/.env` (loaded via `pydantic-settings`).
`get_configs()` in `app/core/config.py` returns a singleton `Config` instance.

**Call `get_configs()` inside functions only** — never at module import time,
or it breaks tests and Alembic migrations.

Config is composed from 13 classes (all in `app/core/config.py`):
`EnvironmentConfig`, `AppConfig`, `CORSConfig`, `SystemConfig`, `SecurityConfig`,
`FileLoggerConfig`, `ConsoleLoggerConfig`, `DatabaseConfig`, `PostgresConfig`,
`ObjectStorageConfig`, `MinioConfig`, `S3StorageConfig`, `GoogleOAuthConfig`,
`RedisConfig`, `MailConfig`.

To add a new setting: add a `Field(...)` to the appropriate config class.

## Auth Guards

Available as typed `Annotated` aliases in `deps.py`:

- `CurrentUser` — validates Bearer JWT, returns active `UserEntity`
- `AdminUser` — requires `role == UserRole.ADMIN` (raises 403 otherwise)

```python
@router.get("/profile")
async def get_profile(user: CurrentUser) -> ProfileResponse:
    ...
```

## Celery Tasks

- App definition: `app/infrastructure/tasks/celery_app.py`
- Task modules: `app/infrastructure/tasks/email_tasks.py`
- Two queues: `mail` (pattern `email.*`) and `default` (everything else)
- Start worker: `make worker`; monitor at `http://localhost:5555` (Flower)

To add a task: create it in `app/infrastructure/tasks/`, add the module to the
`include` list in `create_celery()` in `celery_app.py`.

## Database Migrations

Migrations live in `backend/migrations/versions/`.

**CRITICAL:** When adding a new ORM model, import it in `backend/migrations/env.py`
alongside the existing model imports. Alembic only detects models that are
imported before `target_metadata = Base.metadata`.

Workflow:

```bash
make migrate msg="add book table"   # generates file — review it before applying
make upgrade                        # apply migrations
make downgrade                      # roll back last migration if needed
```

## Testing

**Unit tests** (`tests/unit/`, marker `unit`):

- Fake in-memory repositories that implement the same `ABC` interface
- No mocking framework, no database
- Test use cases directly: instantiate use case with fake repos, call `execute()`, assert result
- Convention: `test_<module>.py`, class `Test<Feature>`, method `test_<scenario>`

**Integration tests** (`tests/integration/`, marker `integration`):

- Require a running PostgreSQL instance
- Currently empty — green-field area

Coverage: `make test-cov` → HTML report in `backend/htmlcov/`.

## Quality Checks

Run before every backend commit:

```bash
make be-check    # ruff lint + format check + mypy (all three)
```

Auto-fix formatting:

```bash
make be-format   # ruff format + import sort (writes files)
```

**Suppressed ruff rules — do not re-enable them:**

- `B008` — `Depends()` in default args is the FastAPI pattern
- `TCH` — `TYPE_CHECKING` blocks break FastAPI's runtime dependency resolution
- `UP042` — `StrEnum` + `str` pattern is intentional across the codebase
- `N818` — `DomainException` base class name is intentional

mypy runs in `strict = True` mode. Use `from __future__ import annotations` at
the top of every file. Type-ignore comments must include the error code:
`# type: ignore[assignment]`, never bare `# type: ignore`.

## Known Constraints

- **`bcrypt` pinned to `<4.0.0`** — bcrypt 4.x+ broke `passlib` compatibility. Do not upgrade.
- **UUIDs are UUIDv7** — use `str(uuid7())` from `uuid_extension`, not `str(uuid.uuid4())`. Preserves insert-order locality in the database.
- **ISBN test value** — use `"1234567890123"`, not `"0000000000000"` (all-zeros passes the ISBN-13 checksum).
- **`session.commit()` belongs in use cases only** — repositories must not commit.
- **`get_configs()` inside functions only** — module-level calls break Alembic and test isolation.

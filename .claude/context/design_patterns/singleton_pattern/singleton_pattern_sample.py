from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

# Custom Types
# Replaces sqlalchemy.ext.asyncio types for mock/illustration purposes.
# In production, these would be AsyncEngine, AsyncSession, async_sessionmaker.

type AsyncEngine = dict[str, Any]
# Represents the database engine — holds connection pool configuration.
# In production: sqlalchemy.ext.asyncio.AsyncEngine

type AsyncSession = dict[str, Any]
# Represents a single database session scoped to one request or operation.
# In production: sqlalchemy.ext.asyncio.AsyncSession

type SessionFactory = Any
# Represents the session factory (async_sessionmaker) that produces AsyncSessions.
# In production: sqlalchemy.ext.asyncio.async_sessionmaker[AsyncSession]


# stub — Configs
# Replaces `from app.core.config import get_configs`.
# Simulates a hardcoded config object as if loaded from environment variables.
class StubConfigs:
    POSTGRES_URI: str = "localhost:5432/bukoo"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    APP_DEBUG: bool = True


def get_configs() -> StubConfigs:
    # In production: reads from .env via pydantic-settings
    print("[get_configs] Loading application configuration (stub)...")
    return StubConfigs()


# stub — Engine factory
# Replaces `create_async_engine(...)` from sqlalchemy.
def create_async_engine(
    url: str, pool_size: int, max_overflow: int, echo: bool
) -> AsyncEngine:
    # In production: creates a real SQLAlchemy AsyncEngine with a connection pool.
    print(f"[create_async_engine] Creating engine for URL: {url}")
    print(
        f"[create_async_engine] pool_size={pool_size}, max_overflow={max_overflow}, echo={echo}"
    )
    return {
        "url": url,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "echo": echo,
        "status": "ready",
    }


# stub — Session factory
# Replaces `async_sessionmaker(...)` from sqlalchemy.
class async_sessionmaker:
    """
    Stub session factory.
    In production: sqlalchemy.ext.asyncio.async_sessionmaker[AsyncSession].
    Calling an instance of this class yields a new AsyncSession context manager.
    """

    def __init__(self, bind: AsyncEngine, expire_on_commit: bool) -> None:
        self._engine = bind
        self._expire_on_commit = expire_on_commit
        print("[async_sessionmaker] Session factory created and bound to engine.")
        print(f"[async_sessionmaker] expire_on_commit={expire_on_commit}")

    def __call__(self):
        # Returns a stub async context manager that yields a stub AsyncSession.
        return StubSessionContext(self._engine)


class StubSessionContext:
    """
    Stub async context manager — simulates `async with session_factory() as session`.
    In production, this opens a real database connection from the pool.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def __aenter__(self) -> AsyncSession:
        print("[StubSessionContext] Opening new AsyncSession from pool...")
        # Returns a stub session dict simulating a live database session.
        return {"engine": self._engine, "status": "open", "dirty": False}

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            print(
                f"[StubSessionContext] Exception detected ({exc_type.__name__}). Session ready for rollback."
            )
        else:
            print("[StubSessionContext] Session closed and returned to pool.")


# singleton class — DatabaseManager
class DatabaseManager:
    # Class-level private attribute — shared across all calls.
    # Holds the single instance once created; None before first call.
    _instance: DatabaseManager | None = None

    def __init__(self) -> None:
        # Guard clause: prevents direct instantiation after the singleton is set.
        # Any attempt to call DatabaseManager() directly after the first creation
        # raises an error, enforcing use of get_instance().
        if DatabaseManager._instance is not None:
            raise RuntimeError(
                "[DatabaseManager] Direct instantiation blocked. "
                "Use DatabaseManager.get_instance() instead."
            )

        print("[DatabaseManager.__init__] First instantiation — running constructor...")

        # Load application configuration (database URI, debug flag, etc.)
        configs = get_configs()
        assert configs.POSTGRES_URI, "POSTGRES_URI must be configured."

        db_url = f"{configs.POSTGRES_ASYNC_PREFIX}{configs.POSTGRES_URI}"
        print(f"[DatabaseManager.__init__] Resolved database URL: {db_url}")

        # Create the async engine — establishes the connection pool.
        # This is the costly operation that must only happen once.
        self.engine: AsyncEngine = create_async_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            echo=configs.APP_DEBUG,
        )

        # Create the session factory — bound to the engine above.
        # All AsyncSessions in the app are produced by this single factory.
        self.session_factory: SessionFactory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

        print(
            "[DatabaseManager.__init__] Engine and session factory initialised successfully."
        )

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        """
        Singleton access point.

        First call:       _instance is None → constructor runs → instance cached.
        Subsequent calls: _instance is set  → cached instance returned immediately.

        All callers — repositories, services, background workers — go through
        this method. No caller ever calls DatabaseManager() directly.
        """
        if cls._instance is None:
            # First call: no instance exists yet — create and cache it.
            print(
                "[DatabaseManager.get_instance] _instance is None. Creating new instance..."
            )
            cls._instance = cls()
            print(
                "[DatabaseManager.get_instance] Singleton instance created and cached."
            )
        else:
            # Subsequent call: instance already exists — return it immediately.
            print(
                "[DatabaseManager.get_instance] _instance already exists. Returning cached singleton."
            )

        return cls._instance


# Inject session scope logic (required in FastAPI)
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a request-scoped AsyncSession via the singleton's session factory.

    - Obtains the singleton via get_instance() (reuses cached instance).
    - Opens a new session from the shared session factory.
    - Yields the session to the caller (e.g., a repository or use case).
    - Rolls back automatically if any exception is raised within the block.
    - Closes and returns the session to the pool on exit.
    """
    print("[session_scope] Requesting singleton via get_instance()...")

    # Singleton reuse: get_instance() returns the cached instance on every call
    # after the first — no engine or session factory is re-created.
    db_manager = DatabaseManager.get_instance()

    print("[session_scope] Opening session via session_factory()...")
    async with db_manager.session_factory() as session:
        try:
            yield session  # caller performs its database operations here
        except Exception as e:
            print(f"[session_scope] Exception caught: {e}. Rolling back session...")
            await session.rollback()  # type: ignore[attr-defined]
            raise


# Inject db session logic (required in FastAPI)
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession for the duration of a request.
    Delegates entirely to session_scope() — the session lifecycle is managed there.

    Usage in a route:
        async def my_route(session: Annotated[AsyncSession, Depends(get_db_session)]):
            ...
    """
    print("[get_db_session] Dependency called — delegating to session_scope()...")
    async with session_scope() as session:
        yield session


# stub — BookRepository
# Simulates a repository using the session to query the database.
# Demonstrates how a downstream consumer uses the singleton indirectly
# via get_db_session() / session_scope().
class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[dict]:
        print("[BookRepository.find_all] Executing query: SELECT * FROM books...")
        # In production: result = await self._session.execute(select(Book))
        # Stub: return mock book records
        return [
            {"id": "book-uuid-001", "title": "Clean Architecture", "price": 79.90},
            {"id": "book-uuid-002", "title": "Design Patterns", "price": 89.90},
        ]


# Entry point — Simulates two separate requests to demonstrate both scenarios:
#   Scenario 1 (Startup): First call to get_instance() — singleton is created.
#   Scenario 2 (Request): Subsequent call — cached singleton is reused.
async def main():
    # Scenario 1: Application startup — first call to get_instance().
    # The constructor runs, engine is created, session factory is set up.
    print("\n" + "=" * 60)
    print("SCENARIO 1: Application Startup — First get_instance() call")
    print("=" * 60)
    db1 = DatabaseManager.get_instance()
    print(f"[main] Singleton id: {id(db1)}\n")

    # Scenario 2: Incoming HTTP request — GET /books.
    # get_instance() is called again inside session_scope().
    # The cached singleton is returned — no engine re-creation.
    # The session factory opens a new scoped session for the request.
    print("=" * 60)
    print("SCENARIO 2: Incoming Request — GET /books (singleton reuse)")
    print("=" * 60)

    # Simulate FastAPI injecting a session via get_db_session()
    session_gen = get_db_session()
    session = await session_gen.__anext__()

    repo = BookRepository(session=session)
    books = await repo.find_all()

    print(f"[main] Books retrieved: {books}")

    # Simulate end of request — close the generator (triggers session cleanup)
    try:
        await session_gen.__anext__()
    except StopAsyncIteration:
        pass

    # Confirm both calls returned the exact same singleton instance
    db2 = DatabaseManager.get_instance()
    print(
        f"\n[main] db1 is db2: {db1 is db2}  ← same singleton instance across both scenarios"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

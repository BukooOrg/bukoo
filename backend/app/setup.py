from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import anyio
import fastapi
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.application.use_cases.system.system_register import SystemRegisterUseCase
from app.core.config import (
    AppConfig,
    CORSConfig,
    EnvironmentConfig,
    EnvironmentOption,
)
from app.domain.exceptions.base import DomainException
from app.infrastructure.db.session import session_scope
from app.presentation.dependencies.deps import (
    get_account_repository,
    get_password_hasher,
    get_user_repository,
)
from app.presentation.http.base_handler import (
    domain_exception_handler,
)
from app.presentation.http.validation_handler import (
    validation_exception_handler,
)
from app.presentation.middlewares import (
    # ClientCacheMiddleware,
    RequestContextMiddleware,
    ResponseFormatterMiddleware,
)


class AppFactory:
    # # cache
    # @staticmethod
    # async def _create_redis_cache_pool() -> None:
    #     cache.pool = redis.ConnectionPool.from_url(settings.REDIS_CACHE_URL)
    #     cache.client = redis.Redis.from_pool(cache.pool)  # type: ignore

    # @staticmethod
    # async def _close_redis_cache_pool() -> None:
    #     if cache.client is not None:
    #         await cache.client.aclose()  # type: ignore

    # # -------------- queue --------------
    # @staticmethod
    # async def _create_redis_queue_pool() -> None:
    #     queue.pool = await create_pool(
    #         RedisSettings(
    #             host=settings.REDIS_QUEUE_HOST, port=settings.REDIS_QUEUE_PORT
    #         )
    #     )

    # async def close_redis_queue_pool() -> None:
    #     if queue.pool is not None:
    #         await queue.pool.aclose()  # type: ignore

    # # -------------- rate limit --------------
    # @staticmethod
    # async def _create_redis_rate_limit_pool() -> None:
    #     rate_limiter.initialize(settings.REDIS_RATE_LIMIT_URL)  # type: ignore

    # @staticmethod
    # async def _close_redis_rate_limit_pool() -> None:
    #     if rate_limiter.client is not None:
    #         await rate_limiter.client.aclose()  # type: ignore

    # -------------- application --------------
    @staticmethod
    async def _set_threadpool_tokens(number_of_tokens: int = 100) -> None:
        limiter = anyio.to_thread.current_default_thread_limiter()
        limiter.total_tokens = number_of_tokens

    # @staticmethod
    # async def _create_system_admin_user() -> None:

    #     async with anext(get_db_session()) as session:
    #         user_repo = get_user_repository(session)
    #         password_hasher = get_password_hasher()

    #         if await user_repo.count_including_deleted() == 0:
    #             use_case = SystemRegisterUseCase(
    #                 user_repo=user_repo, hasher=password_hasher
    #             )
    #             await use_case.execute()

    @staticmethod
    async def _create_system_admin_user() -> None:
        async with session_scope() as db_session:
            user_repo = get_user_repository(db_session)
            account_repo = get_account_repository(db_session)
            password_hasher = get_password_hasher()

            if await user_repo.count_including_deleted() == 0:
                use_case = SystemRegisterUseCase(
                    db_session=db_session,
                    user_repo=user_repo,
                    account_repo=account_repo,
                    hasher=password_hasher,
                )
                await use_case.execute()

    @staticmethod
    def _lifespan_factory(
        # RedisCacheConfig
        configs: (
            AppConfig
            # | ClientSideCacheConfig
            | CORSConfig
            # | RedisQueueConfig
            # | RedisRateLimiterConfig
            | EnvironmentConfig
        ),
    ) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
        """Factory to create a lifespan async context manager for a FastAPI app."""

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            from asyncio import Event

            initialization_complete = Event()
            app.state.initialization_complete = initialization_complete

            await AppFactory._set_threadpool_tokens()
            await AppFactory._create_system_admin_user()

            try:
                # if isinstance(configs, RedisCacheSettings):
                #     await AppFactory._create_redis_cache_pool()

                # if isinstance(configs, RedisQueueSettings):
                #     await AppFactory._create_redis_queue_pool()

                # if isinstance(configs, RedisRateLimiterSettings):
                #     await AppFactory._create_redis_rate_limit_pool()

                initialization_complete.set()

                yield

            finally:
                pass
                # if isinstance(configs, RedisCacheSettings):
                #     await AppFactory._close_redis_cache_pool()

                # if isinstance(configs, RedisQueueSettings):
                #     await AppFactory._close_redis_queue_pool()

                # if isinstance(configs, RedisRateLimiterSettings):
                #     await AppFactory._close_redis_rate_limit_pool()

        return lifespan

    # main entry
    @staticmethod
    def create_application(
        *,
        router: APIRouter,
        # DatabaseSettings
        # | RedisCacheSettings
        # | AppSettings
        # | ClientSideCacheSettings
        # | CORSSettings
        # | RedisQueueSettings
        # | RedisRateLimiterSettings
        # | EnvironmentSettings
        # RedisCacheConfig
        configs: (
            AppConfig
            # | ClientSideCacheConfig
            | CORSConfig
            # | RedisQueueConfig
            # | RedisRateLimiterConfig
            | EnvironmentConfig
        ),
        lifespan: Callable[[FastAPI], _AsyncGeneratorContextManager[Any]] | None = None,
        **kwargs: Any,
    ) -> FastAPI:
        # --- before creating application ---
        if isinstance(configs, AppConfig):
            to_update = {
                "title": configs.APP_NAME,
                "description": configs.APP_DESCRIPTION,
                "contact": {
                    "name": configs.CONTACT_NAME,
                    "email": configs.CONTACT_EMAIL,
                },
                "license_info": {"name": configs.LICENSE_NAME},
            }
            kwargs.update(to_update)

        if isinstance(configs, EnvironmentConfig):
            kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

        # Use custom lifespan if provided, otherwise use default factory
        if lifespan is None:
            lifespan = AppFactory._lifespan_factory(configs)

        application = FastAPI(lifespan=lifespan, **kwargs)
        application.include_router(router)

        # if isinstance(configs, ClientSideCacheSettings):
        #     application.add_middleware(
        #         ClientCacheMiddleware, max_age=configs.CLIENT_CACHE_MAX_AGE
        #     )

        if isinstance(configs, CORSConfig):
            application.add_middleware(
                CORSMiddleware,
                allow_origins=configs.CORS_ORIGINS,
                allow_credentials=True,
                allow_methods=configs.CORS_METHODS,
                allow_headers=configs.CORS_HEADERS,
            )

        application.add_middleware(RequestContextMiddleware)
        application.add_middleware(ResponseFormatterMiddleware)

        application.add_exception_handler(
            RequestValidationError, validation_exception_handler
        )
        application.add_exception_handler(DomainException, domain_exception_handler)

        if (
            isinstance(configs, EnvironmentConfig)
            and configs.ENVIRONMENT != EnvironmentOption.PRODUCTION
        ):
            docs_router = APIRouter()
            if configs.ENVIRONMENT != EnvironmentOption.LOCAL:
                docs_router = APIRouter(
                    # dependencies=[Depends(get_current_superuser)]
                )

            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> dict[str, Any]:
                out: dict[str, Any] = get_openapi(
                    title=application.title,
                    version=application.version,
                    routes=application.routes,
                )
                return out

            application.include_router(docs_router)

        return application

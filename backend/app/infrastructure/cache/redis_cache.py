from __future__ import annotations

from typing import override

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from app.application.interfaces.cache_service import ICacheService
from app.core.config import get_configs
from app.domain.exceptions import CacheDeleteError, CacheReadError, CacheWriteError

# todo: move to appropriate location
_KEY_PREFIX = "bukoo:"


class RedisCacheService(ICacheService):
    """Redis-backed cache service.

    Uses a shared connection pool (max 20 connections) and DB 1 to keep
    cache data isolated from the Celery broker on DB 0.
    """

    def __init__(self) -> None:
        configs = get_configs()
        pool = ConnectionPool.from_url(
            configs.CACHE_REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
        self._client = Redis(connection_pool=pool)

    @override
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        try:
            await self._client.set(_KEY_PREFIX + key, value, ex=ttl_seconds)
        except RedisError as exc:
            raise CacheWriteError(key, str(exc)) from exc

    @override
    async def get(self, key: str) -> str | None:
        try:
            result: str | None = await self._client.get(_KEY_PREFIX + key)
            return result
        except RedisError as exc:
            raise CacheReadError(key, str(exc)) from exc

    @override
    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(_KEY_PREFIX + key)
        except RedisError as exc:
            raise CacheDeleteError(key, str(exc)) from exc

    @override
    async def exists(self, key: str) -> bool:
        try:
            count: int = await self._client.exists(_KEY_PREFIX + key)
            return count > 0
        except RedisError as exc:
            raise CacheReadError(key, str(exc)) from exc

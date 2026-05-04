import json

import redis.asyncio as aioredis

from hify.core.config import settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端单例。必须在 startup 之后调用。"""
    if _client is None:
        raise RuntimeError("Redis client not initialized")
    return _client


async def init_redis() -> None:
    """初始化 Redis 连接（在 lifespan startup 时调用）。"""
    global _client
    _client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis() -> None:
    """关闭 Redis 连接（在 lifespan shutdown 时调用）。"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


class RedisUtil:
    """Redis 工具类。key 用 str，value 自动 JSON 序列化/反序列化。"""

    def __init__(self, redis: aioredis.Redis | None = None):
        self._redis = redis

    @property
    def redis(self) -> aioredis.Redis:
        return self._redis or get_redis()

    async def get(self, key: str) -> dict | list | str | int | float | None:
        """获取值，自动 JSON 反序列化。"""
        raw = await self.redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(
        self,
        key: str,
        value: dict | list | str | int | float,
        expire: int | None = None,
    ) -> None:
        """设置值，自动 JSON 序列化。expire 单位为秒。"""
        serialized = json.dumps(value, ensure_ascii=False)
        if expire is not None:
            await self.redis.set(key, serialized, ex=expire)
        else:
            await self.redis.set(key, serialized)

    async def delete(self, *keys: str) -> int:
        """删除一个或多个 key，返回删除数量。"""
        return await self.redis.delete(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置 key 过期时间（秒）。"""
        return await self.redis.expire(key, seconds)

    async def exists(self, *keys: str) -> int:
        """检查 key 是否存在，返回存在的数量。"""
        return await self.redis.exists(*keys)

    async def incr(self, key: str, amount: int = 1) -> int:
        """自增。"""
        return await self.redis.incr(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """自减。"""
        return await self.redis.decr(key, amount)

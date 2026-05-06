from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from hify.core.config import settings
from hify.core.database import engine
from hify.core.redis import close_redis, init_redis
from hify.shared.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：startup 初始化连接，shutdown 释放资源。"""
    setup_logging(settings.LOG_LEVEL)
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()

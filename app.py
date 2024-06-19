from api.routers import router
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache

from fastapi_cache.backends.redis import RedisBackend

from redis import asyncio as aioredis
from config import REDIS_HOST
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(f"redis://{REDIS_HOST}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    await redis.set("successful_tasks", 0)
    yield


app = FastAPI(lifespan=lifespan, docs_url="/", title="Домашка по DevOPS")

app.include_router(router)


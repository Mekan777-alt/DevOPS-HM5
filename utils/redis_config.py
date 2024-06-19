import logging
import json
from redis import asyncio as aioredis
from config import REDIS_HOST, REDIS_PORT

logging.basicConfig(level=logging.INFO)


async def send_task_to_redis(task):
    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    logging.info("Connected to Redis")
    await redis.lpush("task_queue", json.dumps(task))
    logging.info("Task added to Redis")

import aiormq
import logging
import json

from aio_pika import connect, Message
from fastapi import BackgroundTasks
from redis import asyncio as aioredis
from config import RABBITMQ_HOST, RABBITMQ_PORT, REDIS_HOST, REDIS_PORT

logging.basicConfig(level=logging.INFO)


async def send_rabbitmq_message(msg, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        send_rabbitmq_message_async, msg
    )


async def send_rabbitmq_message_async(msg):
    try:
        connection = await connect(f"amqp://guest:guest@{RABBITMQ_HOST}:{RABBITMQ_PORT}")
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(json.dumps(msg).encode("utf-8")),
            routing_key="fastapi_task"
        )

        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        await redis.incr("successful_tasks")

        await connection.close()
    except aiormq.exceptions.AMQPConnectionError as e:
        logging.error(f"Error connecting to RabbitMQ: {e}")
    except Exception as e:
        logging.error(f"Error sending message to RabbitMQ: {e}")

import os

from dotenv import load_dotenv

load_dotenv()


REDIS_HOST = os.getenv('APP_REDIS_HOST')
REDIS_PORT = os.getenv('APP_REDIS_PORT')

RABBITMQ_HOST = os.getenv('APP_RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('APP_RABBITMQ_PORT')

import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from redis import asyncio as aioredis

from schema import Task
from utils import send_rabbitmq_message, send_task_to_redis
from config import REDIS_HOST, REDIS_PORT

router = APIRouter(
    prefix="/api/v1",
    tags=["Проверка"],
)

logging.basicConfig(level=logging.INFO)


@router.post("/add-task", summary="Проверка работы RabbitMQ и Redis")
async def add_task_endpoint(background_tasks: BackgroundTasks, task: Task = Body(
    ..., example={
        "name": "Task name",
        "description": "Task description",
        "params": {
            "param1": "value1",
            "param2": "value2",
        }
    }
)):
    try:
        task_id = str(uuid.uuid4())
        task_data = task.dict()
        task_data["taskID"] = task_id

        await send_rabbitmq_message(task_data, background_tasks)
        await send_task_to_redis(task_data)

        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content={"message": "Задача успешно добавлена", "taskID": task_id})

    except HTTPException as e:
        return HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/get-stats", summary="Возвращает количество отправленных задач")
async def get_my_tasks():
    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    count = await redis.get("successful_tasks")
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"tasks_count": int(count.decode("utf-8")) if count else 0})


@router.get("/get-task-queue", summary="Возвращает очередь задач из Redis")
async def get_task_queue():

    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    tasks = await redis.lrange("task_queue", 0, -1)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"tasks": [task.decode("utf-8") for task in tasks]})


@router.put("/update-task/{taskID}", summary="Обновить задачу в очереди Redis")
async def update_task(taskID: str,
                      task: Task = Body(..., example={
                          "name": "Task name",
                          "description": "Task description",
                          "params": {
                              "param1": "value1",
                              "param2": "value2",
                          }
                      })):
    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    try:
        tasks = await redis.lrange("task_queue", 0, -1)
        for index, t in enumerate(tasks):
            existing_task = Task.parse_raw(t.decode("utf-8"))
            if existing_task.taskID == taskID:
                task_data = task.dict()
                task_data["taskID"] = taskID
                await redis.lset("task_queue", index, str(task_data))
                updated_tasks = await redis.lrange("task_queue", 0, -1)
                return JSONResponse(status_code=status.HTTP_200_OK, content={
                    "message": "Задача успешно обновлена",
                    "tasks": [t.decode("utf-8") for t in updated_tasks]
                })
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    except aioredis.RedisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера Redis: {str(e)}")


@router.delete("/delete-task/{taskID}", summary="Удалить задачу из очереди Redis")
async def delete_task(taskID: str):
    redis = aioredis.from_url(f"redis://{REDIS_HOST}")
    try:
        tasks = await redis.lrange("task_queue", 0, -1)
        for t in tasks:
            existing_task = Task.parse_raw(t.decode("utf-8"))
            if existing_task.taskID == taskID:
                await redis.lrem("task_queue", 0, t)
                updated_tasks = await redis.lrange("task_queue", 0, -1)
                return JSONResponse(status_code=status.HTTP_200_OK, content={
                    "message": "Задача успешно удалена",
                    "tasks": [t.decode("utf-8") for t in updated_tasks]
                })
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    except aioredis.RedisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера Redis: {str(e)}")

from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.tasks.celery_app import celery_app
from app.schemas.task import TaskOut

router = APIRouter(tags=["tasks"])


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    status = task_result.status
    result = None
    if task_result.ready():
        try:
            result = task_result.result
            if isinstance(result, Exception):
                result = str(result)
        except Exception:
            result = None
    return TaskOut(task_id=task_id, status=status, result=result)

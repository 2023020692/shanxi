from celery import Celery
from app.config import settings

celery_app = Celery(
    "shanxi_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.raster_tasks", "app.tasks.report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
)

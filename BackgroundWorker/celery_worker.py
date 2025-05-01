from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# os.environ['REDIS_URL']
# REDIS_URL = "redis://red-d05pmaa4d50c73f9cnsg:6379"
celery_app = Celery(__name__, broker=redis_url, backend=redis_url)
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)
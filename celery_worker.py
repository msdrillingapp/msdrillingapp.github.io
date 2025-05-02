# from celery import Celery
# import os
#
# redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# # os.environ['REDIS_URL']
# # REDIS_URL = "redis://red-d05pmaa4d50c73f9cnsg:6379"
# celery_app = Celery(__name__, broker=redis_url, backend=redis_url)
# celery_app.conf.update(
#     task_serializer='json',
#     result_serializer='json',
#     accept_content=['json']
# )

from celery import Celery
import os
from main import app

# Example Redis URL: redis://localhost:6379/0 or from env
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
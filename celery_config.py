from celery import Celery
import os
import logging
from celery.signals import after_setup_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Example Redis URL: redis://localhost:6379/0 or from env
redis_url = os.getenv("REDIS_URL", "")

celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
)
celery_app.autodiscover_tasks(["functions.generate_all_pdfs_task"])
celery_app.conf.result_backend = redis_url
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
)



@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logger.setLevel(logging.INFO)  # Ensure logging level is set
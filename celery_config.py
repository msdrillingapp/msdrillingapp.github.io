from celery import Celery
import os
import logging
from celery.signals import after_setup_logger, after_setup_task_logger

# Set up basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

redis_url = os.getenv("REDIS_URL", "")

celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
)


def setup_celery_logging(**kwargs):
    # Create a consistent formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure all loggers use this format
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
# Connect to both signals
after_setup_logger.connect(setup_celery_logging)
after_setup_task_logger.connect(setup_celery_logging)
# Configure logger for both worker and tasks
# @after_setup_logger.connect
# @after_setup_task_logger.connect
# def setup_loggers(logger, *args, **kwargs):
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler = logging.StreamHandler()
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
#     logger.setLevel(logging.INFO)

celery_app.conf.update(
    worker_hijack_root_logger=False,  # Important!
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30*60,
)

print("CELERY CONFIG LOADED")  # Verify the config file loads
logging.info("ROOT LOGGER TEST")  # Verify root logger works
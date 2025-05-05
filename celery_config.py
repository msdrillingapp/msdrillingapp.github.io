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

celery_app.conf.broker_pool_limit = 10  # Reduce connection pool size
celery_app.conf.broker_transport_options = {
    'max_connections': 20,  # Match your Redis plan
    'visibility_timeout': 3600  # 1 hour
}
celery_app.conf.broker_heartbeat = 30  # 30 seconds
celery_app.conf.broker_connection_retry = True
celery_app.conf.broker_connection_max_retries = 3
celery_app.conf.worker_prefetch_multiplier = 1  # Reduce prefetching

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
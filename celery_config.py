from celery import Celery
import os
import logging


# Set up basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

redis_url = os.getenv("REDIS_URL", "")

# celery_app = Celery(
#     'tasks',
#     broker='redis://localhost:6379/0',
#     backend='redis://localhost:6379/1',
#     include=['functions']  # Explicitly include module with tasks
# )
celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
    include=['functions']
)
celery_app.autodiscover_tasks(['functions'], force=True)
celery_app.conf.worker_pool = 'solo'
celery_app.conf.worker_max_tasks_per_child = 1
celery_app.conf.task_protocol = 1
celery_app.conf.worker_send_task_events = True
celery_app.conf.task_send_sent_event = True


celery_app.conf.broker_pool_limit = 10  # Reduce connection pool size
celery_app.conf.broker_transport_options = {
    'max_connections': 20,  # Match your Redis plan
    'visibility_timeout': 3600  # 1 hour
}
celery_app.conf.broker_heartbeat = 30  # 30 seconds
celery_app.conf.broker_connection_retry = True
celery_app.conf.broker_connection_max_retries = 3
celery_app.conf.worker_prefetch_multiplier = 1  # Reduce prefetching

# def setup_celery_logging(**kwargs):
#     # Create a consistent formatter
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
#     # Ensure all loggers use this format
#     handler = logging.StreamHandler()
#     handler.setFormatter(formatter)
#
#     logger = logging.getLogger()
#     logger.addHandler(handler)
#     logger.setLevel(logging.INFO)
# # Connect to both signals
# after_setup_logger.connect(setup_celery_logging)
# after_setup_task_logger.connect(setup_celery_logging)

# celery_app.conf.update(
#     worker_hijack_root_logger=False,  # Important!
#     task_serializer="json",
#     result_serializer="json",
#     accept_content=["json"],
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_time_limit=30*60,
# )
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Critical for Windows
    task_create_missing_queues=True
)

print("CELERY CONFIG LOADED")  # Verify the config file loads

# @celery_app.task(name='generate_numbers')
# def generate_numbers(a, b):
#     return a + b



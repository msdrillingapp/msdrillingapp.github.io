from celery import Celery
import os
# import io
# import zipfile
# import base64
# import pandas as pd
import logging
# from functions import create_depth_chart,create_time_chart,get_app_root,generate_mwd_pdf

# Set up basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

redis_url = os.getenv("REDIS_URL")

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
celery_app.conf.update(result_backend=redis_url)
#
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


#
# @celery_app.task(name='generate_all_pdfs_task')
# def generate_all_pdfs_task(all_rows, pile_data):
#     # Get logger specifically for this task
#     logger = logging.getLogger('celery.task')
#     logger.propagate = True  # Ensure logs propagate to root
#
#     print("=== TASK STARTED ===")
#
#     zip_buffer = io.BytesIO()
#     # raise Exception("Test error to see if this hits the logs.")
#     with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#         for row in all_rows:
#             pileid = row['PileID']
#             time = row['Time']
#             try:
#                 date = pd.to_datetime(time).date().strftime('%Y-%m-%d')
#             except Exception:
#                 continue
#             pile_info = pile_data[pileid][date]
#             time_fig = create_time_chart(pile_info)
#             depth_fig = create_depth_chart(pile_info)
#             try:
#                 pdf_dict = generate_mwd_pdf(row, time_fig, depth_fig)
#                 pdf_bytes = base64.b64decode(pdf_dict['content'])
#                 zip_file.writestr(pdf_dict['filename'], pdf_bytes)
#                 logger.info(f"Added PDF for pile {pileid} to zip.")
#             except Exception as e:
#                 print(f"PDF generation failed: {str(e)}")
#                 logger.error(f"Failed to generate PDF for pile {pileid}: {e}")
#                 continue
#
#     zip_buffer.seek(0)
#
#     # Save to file
#     root_path = get_app_root()
#     filename = "report.zip"
#     filepath = os.path.join(root_path, "instance", "tmp", filename)
#     os.makedirs(os.path.dirname(filepath), exist_ok=True)
#
#     try:
#         with open(filepath, "wb") as f:
#             f.write(zip_buffer.read())
#         logger.info(f"ZIP file saved to {filepath}")
#     except Exception as e:
#         logger.error(f"Error saving zip file: {e}")
#         return "Error filepath:" + filepath
#
#     print("Returning filename:", filename)
#
#     return filename
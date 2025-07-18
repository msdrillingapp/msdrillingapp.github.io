from celery_config import celery_app
import main_last


if __name__ == '__main__':
    celery_app.worker_main(
        argv=['worker', '--pool=solo', '--loglevel=info']
    )

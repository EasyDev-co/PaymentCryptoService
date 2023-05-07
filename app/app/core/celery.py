from app.core.config import settings
from celery import Celery

celery_app = Celery("worker", broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
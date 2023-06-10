from app.core.containers import CeleryContainer
from app import workers

from celery.signals import task_failure

from app.core.celery import celery_app
from app.core.config import settings, EnvEnum


container = CeleryContainer()
container.wire(packages=[workers])
container.init_resources()


config = container.config.provided()

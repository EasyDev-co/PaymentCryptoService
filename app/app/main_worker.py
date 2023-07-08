from app.core.containers import CeleryContainer
from app import workers

from celery.signals import task_failure

from app.core.celery import celery_app
from app.core.config import settings


container = CeleryContainer()
container.wire(packages=[workers])
container.init_resources()


config = container.config.provided()

celery_app.add_periodic_task(30, container.check_balance_bitcoin_task.provided())
celery_app.add_periodic_task(30, container.send_transaction_task.provided())
celery_app.add_periodic_task(30, container.check_transaction_task.provided())
celery_app.add_periodic_task(30, container.check_trc20_wallets_task.provided())

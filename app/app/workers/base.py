from functools import wraps
from celery import Task
from asgiref.sync import async_to_sync
from app.db.session import SyncSession, scope
from uuid import uuid4


class Base(Task):
    autoretry_for = ( )
    default_retry_delay = 3
    max_retries = 5
    countdown = 5
    retry_kwargs = {}

    def __init__(self, session: SyncSession, *args, **kwargs):
        self.session = session.session
        super().__init__(*args, **kwargs)
        if self.autoretry_for and not hasattr(self, '_orig_run'):
            @wraps(self.run)
            def run(*args, **kwargs):
                try:
                    return self._orig_run(*args, **kwargs)
                except self.autoretry_for as exc:
                    raise self.retry(countdown=self.countdown, max_retries=self.max_retries)

            self._orig_run, self.run = self.run, run

    def __call__(self, *args, **kwargs):
        self.retries = self.request.retries
        return self.run(*args, **kwargs)

    def before_start(self, task_id, *args, **kwargs):
        self.task_id = task_id

    async def proccess(self, *args, **kwargs):
        raise NotImplementedError

    async def life_cycle(self, *args, **kwargs):
        scope.set(str(uuid4()))
        try:
            await self.proccess(*args, **kwargs)
            self.session.commit()
        except self.autoretry_for as exc:
            if self.retries >= self.max_retries:
                await self.on_retries_ecxeeded()
            else:
                raise exc
        finally:
            self.session.close()

    async def on_retries_ecxeeded(self):
        raise NotImplemented

    def run(self, *args, **kwargs):
        async_to_sync(self.life_cycle)(*args, **kwargs)
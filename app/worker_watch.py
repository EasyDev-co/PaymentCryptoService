import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
import subprocess
from threading import Timer

code_dir_to_monitor = "."
celery_working_dir = code_dir_to_monitor
celery_cmdline = 'celery -A app.main_worker worker -l info'.split(" ")
celery_beat_cmdline = 'celery -A app.main_worker beat -l info'.split(" ")


def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator


class CeleryRestartHandler(PatternMatchingEventHandler):
    celery_worker_proc: subprocess.Popen
    celery_beat_proc: subprocess.Popen

    @debounce(5)
    def on_any_event(self, event):
        print("detected change. event = {}".format(event))

        self.celery_beat_proc.terminate()
        self.celery_worker_proc.terminate()
        self.run_beat()
        self.run_worker()

    def run_worker(self):
        os.chdir(celery_working_dir)
        self.celery_worker_proc = subprocess.Popen(celery_cmdline)

    def run_beat(self):
        os.chdir(celery_working_dir)
        self.celery_beat_proc = subprocess.Popen(celery_beat_cmdline)


if __name__ == "__main__":
    event_handler = CeleryRestartHandler(patterns=["*.py"])
    event_handler.run_beat()
    event_handler.run_worker()
    observer = Observer()
    observer.schedule(event_handler, code_dir_to_monitor, recursive=True)
    observer.start()
    print("file change observer started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
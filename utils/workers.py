import threading
from queue import Queue

from utils.process_registry import process_registry


class BackgroundWorker:
    def __init__(self):
        self.tasks = Queue()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            self.thread.start()

    def add_task(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def should_skip_task(self, args, kwargs):
        job_id = args[0] if args else kwargs.get("job_id")
        return bool(job_id and process_registry.is_cancelled(job_id))

    def run(self):
        while self.running:
            func, args, kwargs = self.tasks.get()

            try:
                if not self.should_skip_task(args, kwargs):
                    func(*args, **kwargs)
            except Exception as e:
                print(f"Worker Error: {e}")
            finally:
                self.tasks.task_done()

    def pending_count(self):
        return self.tasks.qsize()


background_worker = BackgroundWorker()
background_worker.start()

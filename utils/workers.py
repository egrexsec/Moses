import threading
from queue import Queue

from utils.config import load_config
from utils.process_registry import process_registry


config = load_config()


class WorkerPool:
    def __init__(self, worker_count=2):
        self.tasks = Queue()
        self.worker_count = worker_count
        self.workers = []
        self.running = False

    def start(self):
        if self.running:
            return

        self.running = True

        for index in range(self.worker_count):
            worker = threading.Thread(
                target=self.run,
                daemon=True,
                name=f"MosesWorker-{index + 1}"
            )

            worker.start()
            self.workers.append(worker)

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

    def active_worker_count(self):
        return len(self.workers)

    def status(self):
        return {
            "workers": self.active_worker_count(),
            "queued_tasks": self.pending_count(),
            "running": self.running,
        }


background_worker = WorkerPool(
    worker_count=config.get("worker_pool_size", 2)
)

background_worker.start()

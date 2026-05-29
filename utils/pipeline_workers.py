import threading
from queue import Queue

from utils.config import load_config
from utils.process_registry import process_registry


config = load_config()


class NamedWorkerPool:
    def __init__(self, name, worker_count=1):
        self.name = name
        self.worker_count = worker_count
        self.tasks = Queue()
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
                name=f"{self.name}-{index + 1}"
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
                print(f"{self.name} Error: {e}")
            finally:
                self.tasks.task_done()

    def pending_count(self):
        return self.tasks.qsize()

    def active_worker_count(self):
        return len(self.workers)

    def status(self):
        return {
            "name": self.name,
            "workers": self.active_worker_count(),
            "queued_tasks": self.pending_count(),
            "running": self.running,
        }


# GPU workers should stay conservative because Demucs can exhaust VRAM.
gpu_worker_pool = NamedWorkerPool(
    name="MosesGPUWorker",
    worker_count=config.get("gpu_worker_pool_size", 1)
)

# CPU workers are intended for future post-processing stages such as waveform,
# spectrogram, ZIP packaging, audio previews, and analysis jobs.
cpu_worker_pool = NamedWorkerPool(
    name="MosesCPUWorker",
    worker_count=config.get("cpu_worker_pool_size", 2)
)

gpu_worker_pool.start()
cpu_worker_pool.start()


def get_pipeline_status():
    return {
        "gpu": gpu_worker_pool.status(),
        "cpu": cpu_worker_pool.status(),
    }

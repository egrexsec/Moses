import threading


class GPUScheduler:
    def __init__(self, max_concurrent_jobs=1):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs = 0
        self.lock = threading.Lock()

    def can_start_job(self):
        with self.lock:
            return self.active_jobs < self.max_concurrent_jobs

    def acquire(self):
        with self.lock:
            if self.active_jobs >= self.max_concurrent_jobs:
                return False

            self.active_jobs += 1
            return True

    def release(self):
        with self.lock:
            if self.active_jobs > 0:
                self.active_jobs -= 1

    def status(self):
        with self.lock:
            return {
                "active_jobs": self.active_jobs,
                "max_jobs": self.max_concurrent_jobs,
            }


gpu_scheduler = GPUScheduler(max_concurrent_jobs=1)

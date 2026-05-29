import subprocess
import threading


class ProcessRegistry:
    def __init__(self):
        self.processes = {}
        self.cancelled_jobs = set()
        self.lock = threading.Lock()

    def register(self, job_id, process):
        with self.lock:
            self.processes[job_id] = process

    def unregister(self, job_id):
        with self.lock:
            self.processes.pop(job_id, None)

    def request_cancel(self, job_id):
        with self.lock:
            self.cancelled_jobs.add(job_id)
            process = self.processes.get(job_id)

        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass

        return True

    def is_cancelled(self, job_id):
        with self.lock:
            return job_id in self.cancelled_jobs

    def clear_cancelled(self, job_id):
        with self.lock:
            self.cancelled_jobs.discard(job_id)

    def active_jobs(self):
        with self.lock:
            return list(self.processes.keys())


process_registry = ProcessRegistry()

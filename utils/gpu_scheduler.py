import threading
import time

from utils.audio import get_audio_info
from utils.config import load_config


MODEL_WEIGHTS = {
    "htdemucs": 1,
    "htdemucs_ft": 2,
    "htdemucs_6s": 3,
}


class GPUScheduler:
    def __init__(self, max_gpu_units=4):
        self.max_gpu_units = max_gpu_units
        self.used_gpu_units = 0
        self.active_jobs = {}
        self.lock = threading.Lock()

    def estimate_units(self, audio_file, model):
        info = get_audio_info(audio_file)
        duration_minutes = 5

        if info:
            duration_minutes = max(info.get("duration_minutes", 5), 1)

        model_weight = MODEL_WEIGHTS.get(model, 1)

        if duration_minutes <= 5:
            duration_weight = 1
        elif duration_minutes <= 10:
            duration_weight = 2
        else:
            duration_weight = 3

        return min(model_weight + duration_weight - 1, self.max_gpu_units)

    def can_start_job(self, required_units):
        with self.lock:
            return self.used_gpu_units + required_units <= self.max_gpu_units

    def acquire(self, job_id, required_units):
        with self.lock:
            if self.used_gpu_units + required_units > self.max_gpu_units:
                return False

            self.used_gpu_units += required_units
            self.active_jobs[job_id] = {
                "units": required_units,
                "started_at": time.time()
            }

            return True

    def release(self, job_id):
        with self.lock:
            job = self.active_jobs.pop(job_id, None)

            if job:
                self.used_gpu_units = max(
                    self.used_gpu_units - job["units"],
                    0
                )

    def status(self):
        with self.lock:
            return {
                "used_gpu_units": self.used_gpu_units,
                "max_gpu_units": self.max_gpu_units,
                "available_gpu_units": self.max_gpu_units - self.used_gpu_units,
                "active_jobs": len(self.active_jobs),
                "jobs": self.active_jobs.copy(),
            }


config = load_config()

gpu_scheduler = GPUScheduler(
    max_gpu_units=config.get("max_gpu_units", 4)
)

from dataclasses import dataclass, field
from pathlib import Path
import threading
import time
import uuid


@dataclass
class StoredJob:
    audio_file: str
    model: str
    mode: str
    export_preset: str
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    song_name: str = ""
    status: str = "queued"
    progress: int = 0
    message: str = "Queued"
    outputs: list = field(default_factory=list)
    zip_file: str | None = None
    practice_track: str | None = None
    vocal_preview: str | None = None
    waveform_image: str | None = None
    band_mix: str | None = None
    metadata: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        self.song_name = Path(self.audio_file).stem


class JobStore:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def create_job(self, audio_file, model, mode, export_preset):
        job = StoredJob(
            audio_file=audio_file,
            model=model,
            mode=mode,
            export_preset=export_preset
        )

        with self.lock:
            self.jobs[job.job_id] = job

        return job

    def get_job(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)

    def update_job(self, job_id, **kwargs):
        with self.lock:
            job = self.jobs.get(job_id)

            if not job:
                return None

            for key, value in kwargs.items():
                setattr(job, key, value)

            job.updated_at = time.time()

            return job

    def summary(self):
        with self.lock:
            jobs = list(self.jobs.values())

        return {
            "total": len(jobs),
            "queued": len([job for job in jobs if job.status == "queued"]),
            "running": len([job for job in jobs if job.status == "running"]),
            "complete": len([job for job in jobs if job.status == "complete"]),
            "failed": len([job for job in jobs if job.status == "failed"]),
        }


job_store = JobStore()

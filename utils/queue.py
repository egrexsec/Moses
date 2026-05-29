from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
import uuid


@dataclass
class MosesJob:
    audio_file: str
    model: str
    mode: str
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    song_name: str = ""
    status: str = "queued"

    def __post_init__(self):
        self.song_name = Path(self.audio_file).stem


class JobQueue:
    def __init__(self):
        self.queue = Queue()
        self.history = []

    def add_job(self, audio_file, model, mode):
        job = MosesJob(audio_file=audio_file, model=model, mode=mode)
        self.queue.put(job)
        self.history.append(job)
        return job

    def pending_count(self):
        return self.queue.qsize()

    def get_next_job(self):
        if self.queue.empty():
            return None

        return self.queue.get()

    def mark_done(self, job):
        job.status = "complete"
        self.queue.task_done()

    def mark_failed(self, job):
        job.status = "failed"
        self.queue.task_done()

    def summary(self):
        total = len(self.history)
        complete = len([job for job in self.history if job.status == "complete"])
        failed = len([job for job in self.history if job.status == "failed"])
        queued = len([job for job in self.history if job.status == "queued"])

        return {
            "total": total,
            "complete": complete,
            "failed": failed,
            "queued": queued,
        }


job_queue = JobQueue()

import itertools
import queue
import threading

from utils.priorities import priority_score


class PriorityWorkerPool:
    def __init__(self, worker_count=1, name="priority-pool"):
        self.worker_count = worker_count
        self.name = name
        self.queue = queue.PriorityQueue()
        self.counter = itertools.count()
        self.running = 0
        self.lock = threading.Lock()

        self.threads = []

        for index in range(worker_count):
            thread = threading.Thread(
                target=self.worker_loop,
                daemon=True,
                name=f"{name}-{index}"
            )
            thread.start()
            self.threads.append(thread)

    def add_task(self, fn, *args, priority="normal"):
        score = priority_score(priority)
        self.queue.put((score, next(self.counter), fn, args))

    def worker_loop(self):
        while True:
            _, _, fn, args = self.queue.get()

            with self.lock:
                self.running += 1

            try:
                fn(*args)
            finally:
                with self.lock:
                    self.running -= 1

                self.queue.task_done()

    def status(self):
        with self.lock:
            running = self.running

        return {
            "workers": self.worker_count,
            "running": running,
            "queued_tasks": self.queue.qsize(),
            "pool_name": self.name,
        }

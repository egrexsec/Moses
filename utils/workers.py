import threading
from queue import Queue


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

    def run(self):
        while self.running:
            func, args, kwargs = self.tasks.get()

            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Worker Error: {e}")

            self.tasks.task_done()


background_worker = BackgroundWorker()
background_worker.start()

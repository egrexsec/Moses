import threading


class ProgressTracker:
    def __init__(self):
        self.current = 0
        self.total = 0
        self.message = "Idle"
        self.lock = threading.Lock()

    def start(self, total):
        with self.lock:
            self.total = total
            self.current = 0
            self.message = "Starting processing..."

    def update(self, current, message):
        with self.lock:
            self.current = current
            self.message = message

    def status(self):
        with self.lock:
            if self.total == 0:
                return "Idle"

            percent = int((self.current / self.total) * 100)

            return (
                f"{percent}% Complete | "
                f"{self.current}/{self.total} | "
                f"{self.message}"
            )


tracker = ProgressTracker()

from utils.priority_queue_worker import PriorityWorkerPool


gpu_priority_pool = PriorityWorkerPool(
    worker_count=2,
    name="gpu-priority-pool"
)

cpu_priority_pool = PriorityWorkerPool(
    worker_count=4,
    name="cpu-priority-pool"
)


def priority_pipeline_status():
    return {
        "gpu": gpu_priority_pool.status(),
        "cpu": cpu_priority_pool.status(),
    }

from utils.config import load_config
from utils.job_store import job_store
from utils.pipeline import run_cpu_postprocess_stage, run_gpu_separation_stage
from utils.pipeline_workers import cpu_worker_pool, gpu_worker_pool, get_pipeline_status
from utils.process_registry import process_registry


config = load_config()


def run_pipeline_job(job_id, device_name="cpu", slow_rate=0.75):
    if process_registry.is_cancelled(job_id):
        job_store.update_job(
            job_id,
            status="cancelled",
            progress=100,
            message="Cancelled before pipeline start"
        )
        return

    gpu_success = run_gpu_separation_stage(
        job_id,
        device_name=device_name
    )

    if not gpu_success:
        return

    if process_registry.is_cancelled(job_id):
        job_store.update_job(
            job_id,
            status="cancelled",
            progress=100,
            message="Cancelled before CPU stage"
        )
        return

    cpu_worker_pool.add_task(
        run_cpu_postprocess_stage,
        job_id,
        device_name,
        slow_rate
    )


def submit_pipeline_job(job_id, device_name="cpu", slow_rate=None):
    if slow_rate is None:
        slow_rate = config.get("slow_playback_rate", 0.75)

    job_store.update_job(
        job_id,
        status="queued",
        progress=0,
        message="Queued for GPU separation stage"
    )

    gpu_worker_pool.add_task(
        run_pipeline_job,
        job_id,
        device_name,
        slow_rate
    )

    return job_id


def pipeline_summary_text():
    status = get_pipeline_status()

    gpu = status["gpu"]
    cpu = status["cpu"]

    return (
        f"GPU Workers: {gpu['workers']} | "
        f"GPU Queue: {gpu['queued_tasks']}\n"
        f"CPU Workers: {cpu['workers']} | "
        f"CPU Queue: {cpu['queued_tasks']}"
    )

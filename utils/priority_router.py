from utils.job_store import job_store
from utils.pipeline import run_cpu_postprocess_stage, run_gpu_separation_stage
from utils.priority_pipeline_workers import cpu_priority_pool, gpu_priority_pool
from utils.process_registry import process_registry



def run_priority_pipeline(job_id, device_name="cpu", slow_rate=0.75):
    job = job_store.get_job(job_id)

    if not job:
        return

    if process_registry.is_cancelled(job_id):
        return

    success = run_gpu_separation_stage(
        job_id,
        device_name=device_name,
    )

    if not success:
        return

    cpu_priority_pool.add_task(
        run_cpu_postprocess_stage,
        job_id,
        device_name,
        slow_rate,
        priority=job.priority,
    )



def submit_priority_job(job_id, device_name="cpu", slow_rate=0.75):
    job = job_store.get_job(job_id)

    if not job:
        return None

    job_store.update_job(
        job_id,
        status="queued",
        progress=0,
        message=f"Queued with priority: {job.priority}"
    )

    gpu_priority_pool.add_task(
        run_priority_pipeline,
        job_id,
        device_name,
        slow_rate,
        priority=job.priority,
    )

    return job_id

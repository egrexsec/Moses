import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from utils.bootstrap import run_bootstrap_checks
from utils.database import fetch_recent_jobs
from utils.gpu_scheduler import gpu_scheduler
from utils.model_manager import models_summary_text
from utils.pipeline_workers import get_pipeline_status
from utils.process_registry import process_registry


def bootstrap_dataframe():
    checks = run_bootstrap_checks()

    rows = []

    for check in checks:
        rows.append({
            "Check": check["name"],
            "Status": "PASS" if check["ok"] else "WARN",
            "Details": check["details"],
            "Fix": "" if check["ok"] else check["fix"],
        })

    return pd.DataFrame(rows)


def gpu_status_text():
    scheduler = gpu_scheduler.status()
    lines = [
        "GPU Scheduler",
        f"Used Units: {scheduler['used_gpu_units']}",
        f"Max Units: {scheduler['max_gpu_units']}",
        f"Available Units: {scheduler['available_gpu_units']}",
        f"Active Reservations: {scheduler['active_jobs']}",
        "",
        "Active GPU Jobs:",
    ]

    if not scheduler["jobs"]:
        lines.append("- None")
    else:
        for job_id, job_data in scheduler["jobs"].items():
            lines.append(f"- {job_id}: {job_data['units']} units")

    return "\n".join(lines)


def worker_status_text():
    status = get_pipeline_status()
    gpu = status["gpu"]
    cpu = status["cpu"]

    return "\n".join([
        "Worker Pools",
        "",
        f"GPU Workers: {gpu['workers']}",
        f"GPU Queue: {gpu['queued_tasks']}",
        f"GPU Running: {gpu['running']}",
        "",
        f"CPU Workers: {cpu['workers']}",
        f"CPU Queue: {cpu['queued_tasks']}",
        f"CPU Running: {cpu['running']}",
    ])


def active_processes_text():
    active = process_registry.active_jobs()

    lines = ["Active Processes", ""]

    if not active:
        lines.append("- None")
    else:
        for job_id in active:
            lines.append(f"- {job_id}")

    return "\n".join(lines)


def recent_jobs_dataframe(limit=25):
    jobs = fetch_recent_jobs(limit=limit)

    if not jobs:
        return pd.DataFrame(columns=["Job ID", "Song", "Status", "Progress", "Message"])

    rows = []

    for job in jobs:
        rows.append({
            "Job ID": job["job_id"],
            "Song": job["song_name"],
            "Status": job["status"],
            "Progress": f"{job['progress']}%",
            "Message": job["message"],
        })

    return pd.DataFrame(rows)


def system_runtime_text():
    ffmpeg_path = shutil.which("ffmpeg") or "Not found"
    ffprobe_path = shutil.which("ffprobe") or "Not found"
    nvidia_path = shutil.which("nvidia-smi") or "Not found"

    lines = [
        "System Runtime",
        "",
        f"FFmpeg: {ffmpeg_path}",
        f"FFprobe: {ffprobe_path}",
        f"NVIDIA SMI: {nvidia_path}",
    ]

    if nvidia_path != "Not found":
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,utilization.gpu", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            lines.extend(["", "NVIDIA GPU:", result.stdout.strip() or result.stderr.strip()])
        except Exception as exc:
            lines.append(f"NVIDIA check failed: {exc}")

    return "\n".join(lines)


def diagnostics_report_text():
    return "\n\n".join([
        system_runtime_text(),
        gpu_status_text(),
        worker_status_text(),
        active_processes_text(),
        models_summary_text(),
    ])


def write_runtime_snapshot(path="logs/runtime_snapshot.json"):
    snapshot = {
        "system": system_runtime_text(),
        "gpu_scheduler": gpu_scheduler.status(),
        "workers": get_pipeline_status(),
        "active_processes": process_registry.active_jobs(),
        "recent_jobs": fetch_recent_jobs(limit=25),
    }

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=4)

    return str(output_path)

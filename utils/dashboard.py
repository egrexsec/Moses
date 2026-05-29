import pandas as pd

from utils.database import fetch_recent_jobs, update_job_status


def get_queue_dashboard(limit=50):
    jobs = fetch_recent_jobs(limit=limit)

    if not jobs:
        return pd.DataFrame(
            columns=[
                "Job ID",
                "Song",
                "Status",
                "Progress",
                "Message"
            ]
        )

    formatted = []

    for job in jobs:
        formatted.append({
            "Job ID": job["job_id"][:8],
            "Song": job["song_name"],
            "Status": job["status"],
            "Progress": f"{job['progress']}%",
            "Message": job["message"]
        })

    return pd.DataFrame(formatted)


def cancel_job(job_id):
    if not job_id:
        return "No job selected."

    update_job_status(job_id, "cancelled", "Cancelled by user")

    return f"Cancelled job: {job_id}"

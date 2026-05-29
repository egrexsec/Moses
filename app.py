import gradio as gr

from utils.async_processing import run_demucs_job
from utils.config import load_config
from utils.job_store import job_store
from utils.mixer import mix_stems
from utils.presets import EXPORT_PRESETS
from utils.process_registry import process_registry
from utils.system import detect_device
from utils.audio import check_ffmpeg
from utils.workers import background_worker

config = load_config()

device_info = detect_device()
ffmpeg_installed = check_ffmpeg()

PRESETS = {
    "Bass Practice": {
        "model": "htdemucs_6s",
        "mode": "4 Stems"
    },
    "Choir Rehearsal": {
        "model": "htdemucs_ft",
        "mode": "Vocals + Instrumental"
    },
    "Standard": {
        "model": config["default_model"],
        "mode": config["default_mode"]
    }
}


def empty_job_outputs(message="No active job."):
    return (
        message,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        gr.update(value=0),
        gr.update(value="Idle")
    )


def apply_preset(preset_name):
    preset = PRESETS[preset_name]
    return preset["model"], preset["mode"]


def queue_single_job(audio_file, model, mode, export_preset):
    job = job_store.create_job(
        audio_file,
        model,
        mode,
        export_preset
    )

    background_worker.add_task(
        run_demucs_job,
        job.job_id,
        device_info["device"],
        config["slow_playback_rate"]
    )

    return job


def submit_job(audio_file, model, mode, export_preset):
    if audio_file is None:
        return "No file uploaded.", "", gr.update(value=0), gr.update(value="Idle")

    if not ffmpeg_installed:
        return "FFmpeg is not installed.", "", gr.update(value=0), gr.update(value="Error")

    job = queue_single_job(audio_file, model, mode, export_preset)

    return (
        f"Job submitted: {job.song_name}",
        job.job_id,
        gr.update(value=0),
        gr.update(value="Queued")
    )


def submit_batch_jobs(audio_files, model, mode, export_preset):
    if not audio_files:
        return "No files uploaded for batch queue."

    queued_jobs = []

    for audio_file in audio_files:
        job = queue_single_job(
            audio_file,
            model,
            mode,
            export_preset
        )

        queued_jobs.append(job.song_name)

    return (
        f"Queued {len(queued_jobs)} jobs: " +
        ", ".join(queued_jobs[:5])
    )


def poll_job(job_id):
    if not job_id:
        return empty_job_outputs()

    job = job_store.get_job(job_id)

    if not job:
        return empty_job_outputs("Job not found.")

    status_text = (
        f"Status: {job.status} | "
        f"Progress: {job.progress}% | "
        f"Message: {job.message}"
    )

    if job.error:
        status_text += f" | Error: {job.error}"

    queue_summary = job_store.summary()

    queue_text = (
        f"Queued: {queue_summary['queued']} | "
        f"Running: {queue_summary['running']} | "
        f"Complete: {queue_summary['complete']} | "
        f"Failed: {queue_summary['failed']}"
    )

    return (
        status_text,
        job.outputs,
        job.metadata,
        job.zip_file,
        job.practice_track,
        job.vocal_preview,
        job.waveform_image,
        getattr(job, "spectrogram_image", None),
        queue_text,
        job.band_mix,
        gr.update(value=job.progress),
        gr.update(value=job.status.title())
    )


def cancel_job(job_id):
    if not job_id:
        return "No job selected."

    process_registry.request_cancel(job_id)

    job_store.update_job(
        job_id,
        status="cancelled",
        progress=100,
        message="Cancellation requested"
    )

    return f"Cancellation requested for job: {job_id}"


def retry_job(job_id):
    job = job_store.get_job(job_id)

    if not job:
        return "Job not found in memory."

    process_registry.clear_cancelled(job_id)

    background_worker.add_task(
        run_demucs_job,
        job.job_id,
        device_info["device"],
        config["slow_playback_rate"]
    )

    job_store.update_job(
        job_id,
        status="queued",
        progress=0,
        message="Retry requested",
        error=""
    )

    return f"Retry queued: {job.song_name}"


def remix_stems(
    stem_files,
    vocals_gain,
    bass_gain,
    drums_gain,
    other_gain,
    mute_vocals,
    mute_bass,
    mute_drums,
    mute_other
):
    if not stem_files:
        return None

    gains = {
        "vocals": vocals_gain,
        "bass": bass_gain,
        "drums": drums_gain,
        "other": other_gain,
    }

    mutes = {
        "vocals": mute_vocals,
        "bass": mute_bass,
        "drums": mute_drums,
        "other": mute_other,
    }

    output_path = "mixes/custom_mix.wav"

    return mix_stems(
        stem_files,
        output_path,
        gains=gains,
        mutes=mutes
    )

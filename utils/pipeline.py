import subprocess
import time
from pathlib import Path

from utils.audio import get_audio_info
from utils.export import create_zip_archive
from utils.gpu_scheduler import gpu_scheduler
from utils.job_store import job_store
from utils.mixer import mix_stems
from utils.music import detect_bpm_and_key
from utils.organization import organize_song_outputs
from utils.playback import create_slowed_version
from utils.preview import get_preview_stems
from utils.presets import filter_stems_by_preset
from utils.process_registry import process_registry
from utils.spectrogram import generate_spectrogram
from utils.stems import categorize_stems
from utils.visualization import generate_waveform_image

OUTPUT_DIR = "separated"
MIX_DIR = Path("mixes")
MIX_DIR.mkdir(exist_ok=True)

class JobCancelled(Exception):
    pass

def check_cancelled(job_id):
    if process_registry.is_cancelled(job_id):
        raise JobCancelled("Job was cancelled by user")

def mark_cancelled(job_id):
    job_store.update_job(job_id, status="cancelled", progress=100, message="Cancelled by user", error="")
    process_registry.unregister(job_id)
    process_registry.clear_cancelled(job_id)

def build_demucs_command(model, mode):
    cmd = ["python", "-m", "demucs", "-n", model, "--out", OUTPUT_DIR]
    if mode == "Vocals + Instrumental":
        cmd += ["--two-stems", "vocals"]
    return cmd

def collect_output_files(model, song_name):
    result_folder = Path(OUTPUT_DIR) / model / song_name
    return list(result_folder.glob("*.wav"))

def build_metadata(audio_file, device_name):
    info = get_audio_info(audio_file)
    music_info = detect_bpm_and_key(audio_file)
    metadata_lines = []
    if info:
        metadata_lines.append(f"Duration: {info['duration_minutes']} minutes")
    if music_info:
        metadata_lines.append(f"Estimated BPM: {music_info['bpm']}")
        metadata_lines.append(f"Estimated Key: {music_info['key']}")
    metadata_lines.append(f"Processing Device: {device_name}")
    return "\n".join(metadata_lines)

def wait_for_gpu_slot(job_id, audio_file, model):
    required_units = gpu_scheduler.estimate_units(audio_file, model)
    while True:
        check_cancelled(job_id)
        if gpu_scheduler.acquire(job_id, required_units):
            scheduler_status = gpu_scheduler.status()
            job_store.update_job(
                job_id,
                status="running",
                progress=5,
                message=f"GPU reserved: {required_units} units | {scheduler_status['used_gpu_units']}/{scheduler_status['max_gpu_units']} used"
            )
            return required_units
        scheduler_status = gpu_scheduler.status()
        job_store.update_job(
            job_id,
            status="queued",
            progress=0,
            message=f"Waiting for GPU resources ({scheduler_status['used_gpu_units']}/{scheduler_status['max_gpu_units']} used)"
        )
        time.sleep(2)

def run_gpu_separation_stage(job_id, device_name="cpu"):
    job = job_store.get_job(job_id)
    if not job:
        return False
    gpu_reserved = False
    try:
        check_cancelled(job_id)
        if device_name == "cuda":
            wait_for_gpu_slot(job_id, job.audio_file, job.model)
            gpu_reserved = True
        job_store.update_job(job_id, status="running", progress=10, message="GPU stage: starting Demucs separation")
        cmd = build_demucs_command(job.model, job.mode)
        cmd.append(job.audio_file)
        process = subprocess.Popen(cmd)
        process_registry.register(job_id, process)
        return_code = process.wait()
        process_registry.unregister(job_id)
        check_cancelled(job_id)
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)
        job_store.update_job(job_id, progress=40, message="GPU stage complete; queued CPU post-processing")
        return True
    except JobCancelled:
        mark_cancelled(job_id)
        return False
    except Exception as e:
        if process_registry.is_cancelled(job_id):
            mark_cancelled(job_id)
        else:
            job_store.update_job(job_id, status="failed", progress=100, message="GPU stage failed", error=str(e))
        return False
    finally:
        process_registry.unregister(job_id)
        if gpu_reserved:
            gpu_scheduler.release(job_id)

def run_cpu_postprocess_stage(job_id, device_name="cpu", slow_rate=0.75):
    job = job_store.get_job(job_id)
    if not job:
        return
    try:
        check_cancelled(job_id)
        job_store.update_job(job_id, status="running", progress=45, message="CPU stage: collecting stems")
        files = collect_output_files(job.model, job.song_name)
        organized_files = organize_song_outputs(job.song_name, files)
        categorized = categorize_stems(organized_files)
        previews = get_preview_stems(organized_files)
        check_cancelled(job_id)
        job_store.update_job(job_id, progress=60, message="CPU stage: generating metadata")
        metadata = build_metadata(job.audio_file, device_name)
        waveform_image = None
        spectrogram_image = None
        if previews.get("vocals"):
            check_cancelled(job_id)
            job_store.update_job(job_id, progress=70, message="CPU stage: waveform")
            waveform_image = generate_waveform_image(previews.get("vocals"))
            check_cancelled(job_id)
            job_store.update_job(job_id, progress=75, message="CPU stage: spectrogram")
            spectrogram_image = generate_spectrogram(previews.get("vocals"))
        practice_track = None
        if previews.get("vocals"):
            check_cancelled(job_id)
            job_store.update_job(job_id, progress=80, message="CPU stage: practice track")
            practice_track = f"exports/{job.song_name}/{job.song_name}_slow_practice.wav"
            create_slowed_version(previews.get("vocals"), practice_track, slow_rate)
        check_cancelled(job_id)
        filtered_outputs = filter_stems_by_preset(categorized, job.export_preset)
        if not filtered_outputs:
            filtered_outputs = organized_files
        band_mix_files = []
        for stem_type in ["bass", "drums", "other"]:
            band_mix_files.extend(categorized.get(stem_type, []))
        band_mix = None
        if band_mix_files:
            check_cancelled(job_id)
            job_store.update_job(job_id, progress=88, message="CPU stage: band mix")
            band_mix = str(MIX_DIR / f"{job.song_name}_band_mix.wav")
            mix_stems(band_mix_files, band_mix)
        check_cancelled(job_id)
        job_store.update_job(job_id, progress=94, message="CPU stage: ZIP export")
        zip_file = create_zip_archive(filtered_outputs, f"{job.song_name}_stems.zip")
        check_cancelled(job_id)
        job_store.update_job(
            job_id,
            status="complete",
            progress=100,
            message="Complete",
            outputs=filtered_outputs,
            zip_file=zip_file,
            practice_track=practice_track,
            vocal_preview=previews.get("vocals"),
            waveform_image=waveform_image,
            spectrogram_image=spectrogram_image,
            band_mix=band_mix,
            metadata=metadata,
            error=""
        )
    except JobCancelled:
        mark_cancelled(job_id)
    except Exception as e:
        if process_registry.is_cancelled(job_id):
            mark_cancelled(job_id)
        else:
            job_store.update_job(job_id, status="failed", progress=100, message="CPU stage failed", error=str(e))

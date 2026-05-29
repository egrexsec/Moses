import subprocess
from pathlib import Path

from utils.audio import get_audio_info
from utils.export import create_zip_archive
from utils.job_store import job_store
from utils.mixer import mix_stems
from utils.music import detect_bpm_and_key
from utils.organization import organize_song_outputs
from utils.playback import create_slowed_version
from utils.preview import get_preview_stems
from utils.presets import filter_stems_by_preset
from utils.spectrogram import generate_spectrogram
from utils.stems import categorize_stems
from utils.visualization import generate_waveform_image


OUTPUT_DIR = "separated"
MIX_DIR = Path("mixes")
MIX_DIR.mkdir(exist_ok=True)


def build_demucs_command(model, mode):
    cmd = [
        "python",
        "-m",
        "demucs",
        "-n",
        model,
        "--out",
        OUTPUT_DIR,
    ]

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


def run_demucs_job(job_id, device_name="cpu", slow_rate=0.75):
    job = job_store.get_job(job_id)

    if not job:
        return

    try:
        job_store.update_job(
            job_id,
            status="running",
            progress=10,
            message="Starting Demucs separation"
        )

        cmd = build_demucs_command(job.model, job.mode)
        cmd.append(job.audio_file)

        subprocess.run(cmd, check=True)

        job_store.update_job(
            job_id,
            progress=45,
            message="Collecting stems"
        )

        files = collect_output_files(job.model, job.song_name)
        organized_files = organize_song_outputs(job.song_name, files)
        categorized = categorize_stems(organized_files)
        previews = get_preview_stems(organized_files)

        job_store.update_job(
            job_id,
            progress=65,
            message="Generating metadata and previews"
        )

        metadata = build_metadata(job.audio_file, device_name)

        waveform_image = None
        spectrogram_image = None

        if previews.get("vocals"):
            waveform_image = generate_waveform_image(previews.get("vocals"))
            spectrogram_image = generate_spectrogram(previews.get("vocals"))

        practice_track = None

        if previews.get("vocals"):
            practice_track = f"exports/{job.song_name}/{job.song_name}_slow_practice.wav"
            create_slowed_version(previews.get("vocals"), practice_track, slow_rate)

        job_store.update_job(
            job_id,
            progress=80,
            message="Creating mixes and exports"
        )

        filtered_outputs = filter_stems_by_preset(categorized, job.export_preset)

        if not filtered_outputs:
            filtered_outputs = organized_files

        band_mix_files = []
        for stem_type in ["bass", "drums", "other"]:
            band_mix_files.extend(categorized.get(stem_type, []))

        band_mix = None

        if band_mix_files:
            band_mix = str(MIX_DIR / f"{job.song_name}_band_mix.wav")
            mix_stems(band_mix_files, band_mix)

        zip_file = create_zip_archive(
            filtered_outputs,
            f"{job.song_name}_stems.zip"
        )

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
            metadata=metadata
        )

    except Exception as e:
        job_store.update_job(
            job_id,
            status="failed",
            progress=100,
            message="Failed",
            error=str(e)
        )

import gradio as gr
import subprocess
from pathlib import Path

from utils.audio import check_ffmpeg, get_audio_info
from utils.system import detect_device
from utils.export import create_zip_archive
from utils.music import detect_bpm_and_key
from utils.organization import organize_song_outputs
from utils.playback import create_slowed_version
from utils.config import load_config
from utils.progress import tracker
from utils.stems import categorize_stems
from utils.preview import get_preview_stems
from utils.queue import job_queue
from utils.visualization import generate_waveform_image
from utils.presets import EXPORT_PRESETS, filter_stems_by_preset
from utils.mixer import mix_stems
from utils.workers import background_worker

OUTPUT_DIR = "separated"
MIX_DIR = Path("mixes")
MIX_DIR.mkdir(exist_ok=True)

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


def apply_preset(preset_name):
    preset = PRESETS[preset_name]
    return preset["model"], preset["mode"]


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


def build_metadata(audio_file):
    info = get_audio_info(audio_file)
    music_info = detect_bpm_and_key(audio_file)

    metadata_lines = []

    if info:
        metadata_lines.append(
            f"Duration: {info['duration_minutes']} minutes"
        )

    if music_info:
        metadata_lines.append(
            f"Estimated BPM: {music_info['bpm']}"
        )
        metadata_lines.append(
            f"Estimated Key: {music_info['key']}"
        )

    metadata_lines.append(
        f"Processing Device: {device_info['device']}"
    )

    return "\n".join(metadata_lines)


def create_practice_track(song_name, organized_files):
    vocals_file = None

    for file in organized_files:
        if "vocals" in file.lower():
            vocals_file = file
            break

    if not vocals_file:
        return None

    slowed_output = f"exports/{song_name}/{song_name}_slow_practice.wav"

    return create_slowed_version(
        vocals_file,
        slowed_output,
        config["slow_playback_rate"]
    )


def create_band_mix(song_name, categorized):
    mix_files = []

    for stem_type in ["bass", "drums", "other"]:
        mix_files.extend(categorized.get(stem_type, []))

    if not mix_files:
        return None

    output_path = MIX_DIR / f"{song_name}_band_mix.wav"

    return mix_stems(
        mix_files,
        str(output_path)
    )


def process_song(audio_file, model, mode):
    job = job_queue.add_job(audio_file, model, mode)

    cmd = build_demucs_command(model, mode)
    cmd.append(audio_file)

    subprocess.run(cmd, check=True)

    files = collect_output_files(model, job.song_name)

    organized_files = organize_song_outputs(job.song_name, files)

    job_queue.mark_done(job)

    return job.song_name, organized_files


def split_song(audio_file, model, mode, export_preset):
    if audio_file is None:
        return (
            "Please upload a song.",
            [],
            "",
            None,
            None,
            None,
            None,
            "",
            None
        )

    if not ffmpeg_installed:
        return (
            "FFmpeg is not installed.",
            [],
            "Install FFmpeg and restart Moses.",
            None,
            None,
            None,
            None,
            "",
            None
        )

    tracker.start(1)
    tracker.update(0, "Processing single song")

    try:
        song_name, organized_files = process_song(
            audio_file,
            model,
            mode
        )
    except subprocess.CalledProcessError as e:
        return f"Error: {e}", [], "", None, None, None, None, "", None

    tracker.update(1, f"Completed {song_name}")

    metadata = build_metadata(audio_file)

    categorized = categorize_stems(organized_files)

    filtered_outputs = filter_stems_by_preset(
        categorized,
        export_preset
    )

    if not filtered_outputs:
        filtered_outputs = organized_files

    practice_track = create_practice_track(
        song_name,
        organized_files
    )

    band_mix = create_band_mix(
        song_name,
        categorized
    )

    zip_file = create_zip_archive(
        filtered_outputs,
        f"{song_name}_stems.zip"
    )

    previews = get_preview_stems(organized_files)

    waveform_image = None

    if previews.get("vocals"):
        waveform_image = generate_waveform_image(
            previews.get("vocals")
        )

    queue_summary = job_queue.summary()

    queue_text = (
        f"Queued: {queue_summary['queued']} | "
        f"Complete: {queue_summary['complete']} | "
        f"Failed: {queue_summary['failed']}"
    )

    return (
        tracker.status(),
        filtered_outputs,
        metadata,
        zip_file,
        practice_track,
        previews.get("vocals"),
        waveform_image,
        queue_text,
        band_mix
    )


with gr.Blocks(title="Moses") as app:
    gr.Markdown("# Moses")
    gr.Markdown("AI-powered Gospel stem splitter using Demucs")

    gr.Markdown(
        f"**Processing Device:** {device_info['device']}"
    )

    if device_info["gpu"]:
        gr.Markdown(f"**GPU:** {device_info['gpu']}")

    gr.Markdown(
        f"**FFmpeg Installed:** {'Yes' if ffmpeg_installed else 'No'}"
    )

    preset = gr.Dropdown(
        choices=list(PRESETS.keys()),
        value="Standard",
        label="Workflow Preset"
    )

    export_preset = gr.Dropdown(
        choices=list(EXPORT_PRESETS.keys()),
        value="MD Pack",
        label="Export Preset"
    )

    model = gr.Dropdown(
        choices=["htdemucs", "htdemucs_ft", "htdemucs_6s"],
        value=config["default_model"],
        label="Model"
    )

    mode = gr.Radio(
        choices=["4 Stems", "Vocals + Instrumental"],
        value=config["default_mode"],
        label="Split Mode"
    )

    preset.change(
        apply_preset,
        inputs=[preset],
        outputs=[model, mode]
    )

    with gr.Tab("Single Song"):
        audio = gr.Audio(type="filepath", label="Upload Song")

        run_button = gr.Button("Split Song")

        status = gr.Textbox(label="Progress")
        outputs = gr.File(label="Separated Stems", file_count="multiple")
        metadata = gr.Textbox(label="Song Information")
        zip_download = gr.File(label="Download ZIP")
        practice_track = gr.File(label="Slow Practice Track")
        vocal_preview = gr.Audio(label="Vocal Preview")
        waveform_preview = gr.Image(label="Waveform Preview")
        queue_status = gr.Textbox(label="Queue Status")
        band_mix_preview = gr.Audio(label="Band Mix Preview")

        run_button.click(
            split_song,
            inputs=[audio, model, mode, export_preset],
            outputs=[
                status,
                outputs,
                metadata,
                zip_download,
                practice_track,
                vocal_preview,
                waveform_preview,
                queue_status,
                band_mix_preview
            ]
        )

app.launch()

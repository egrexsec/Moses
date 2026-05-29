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

OUTPUT_DIR = "separated"

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


def process_song(audio_file, model, mode):
    song_name = Path(audio_file).stem

    cmd = build_demucs_command(model, mode)
    cmd.append(audio_file)

    subprocess.run(cmd, check=True)

    files = collect_output_files(model, song_name)

    organized_files = organize_song_outputs(song_name, files)

    return song_name, organized_files


def split_song(audio_file, model, mode):
    if audio_file is None:
        return "Please upload a song.", [], "", None, None, None

    if not ffmpeg_installed:
        return (
            "FFmpeg is not installed.",
            [],
            "Install FFmpeg and restart Moses.",
            None,
            None,
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
        return f"Error: {e}", [], "", None, None, None

    tracker.update(1, f"Completed {song_name}")

    metadata = build_metadata(audio_file)

    practice_track = create_practice_track(
        song_name,
        organized_files
    )

    zip_file = create_zip_archive(
        organized_files,
        f"{song_name}_stems.zip"
    )

    previews = get_preview_stems(organized_files)

    return (
        tracker.status(),
        organized_files,
        metadata,
        zip_file,
        practice_track,
        previews.get("vocals")
    )


def batch_split(audio_files, model, mode):
    if not audio_files:
        return "Please upload songs.", [], "", None

    if not ffmpeg_installed:
        return (
            "FFmpeg is not installed.",
            [],
            "Install FFmpeg and restart Moses.",
            None
        )

    all_outputs = []
    processed = []

    tracker.start(len(audio_files))

    for index, audio_file in enumerate(audio_files, start=1):
        tracker.update(index - 1, f"Processing {Path(audio_file).stem}")

        try:
            song_name, organized_files = process_song(
                audio_file,
                model,
                mode
            )
        except subprocess.CalledProcessError:
            continue

        all_outputs.extend(organized_files)
        processed.append(song_name)

        tracker.update(index, f"Completed {song_name}")

    categorized = categorize_stems(all_outputs)

    summary = (
        f"Processed {len(processed)} songs\n"
        f"Device: {device_info['device']}\n"
        f"Vocals: {len(categorized.get('vocals', []))}\n"
        f"Bass: {len(categorized.get('bass', []))}\n"
        f"Drums: {len(categorized.get('drums', []))}"
    )

    zip_file = create_zip_archive(
        all_outputs,
        "moses_batch_stems.zip"
    )

    return (
        tracker.status(),
        all_outputs,
        summary,
        zip_file
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

        run_button.click(
            split_song,
            inputs=[audio, model, mode],
            outputs=[
                status,
                outputs,
                metadata,
                zip_download,
                practice_track,
                vocal_preview
            ]
        )

    with gr.Tab("Batch Processing"):
        batch_audio = gr.Files(label="Upload Multiple Songs")

        batch_button = gr.Button("Batch Split")

        batch_status = gr.Textbox(label="Batch Progress")
        batch_outputs = gr.File(label="Batch Outputs", file_count="multiple")
        batch_metadata = gr.Textbox(label="Batch Summary")
        batch_zip = gr.File(label="Download Batch ZIP")

        batch_button.click(
            batch_split,
            inputs=[batch_audio, model, mode],
            outputs=[
                batch_status,
                batch_outputs,
                batch_metadata,
                batch_zip
            ]
        )

app.launch()

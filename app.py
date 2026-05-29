import gradio as gr
import subprocess
from pathlib import Path

from utils.audio import check_ffmpeg, get_audio_info
from utils.system import detect_device

OUTPUT_DIR = "separated"


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
        "model": "htdemucs",
        "mode": "4 Stems"
    }
}


def apply_preset(preset_name):
    preset = PRESETS[preset_name]
    return preset["model"], preset["mode"]


def split_song(audio_file, model, mode):
    if audio_file is None:
        return "Please upload a song.", [], ""

    if not ffmpeg_installed:
        return "FFmpeg is not installed.", [], "Install FFmpeg and restart Moses."

    info = get_audio_info(audio_file)

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

    cmd.append(audio_file)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return f"Error: {e}", [], ""

    song_name = Path(audio_file).stem
    result_folder = Path(OUTPUT_DIR) / model / song_name

    files = list(result_folder.glob("*.wav"))

    metadata = ""

    if info:
        metadata = (
            f"Duration: {info['duration_minutes']} minutes\n"
            f"Processing Device: {device_info['device']}"
        )

    return "Stem separation complete.", [str(f) for f in files], metadata


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

    audio = gr.Audio(type="filepath", label="Upload Song")

    model = gr.Dropdown(
        choices=["htdemucs", "htdemucs_ft", "htdemucs_6s"],
        value="htdemucs",
        label="Model"
    )

    mode = gr.Radio(
        choices=["4 Stems", "Vocals + Instrumental"],
        value="4 Stems",
        label="Split Mode"
    )

    preset.change(
        apply_preset,
        inputs=[preset],
        outputs=[model, mode]
    )

    run_button = gr.Button("Split Song")

    status = gr.Textbox(label="Status")
    outputs = gr.File(label="Separated Stems", file_count="multiple")
    metadata = gr.Textbox(label="Song Information")

    run_button.click(
        split_song,
        inputs=[audio, model, mode],
        outputs=[status, outputs, metadata]
    )

app.launch()

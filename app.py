import gradio as gr
import subprocess
from pathlib import Path

OUTPUT_DIR = "separated"


def split_song(audio_file, model, mode):
    if audio_file is None:
        return "Please upload a song.", []

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
        return f"Error: {e}", []

    song_name = Path(audio_file).stem
    result_folder = Path(OUTPUT_DIR) / model / song_name

    files = list(result_folder.glob("*.wav"))

    return "Stem separation complete.", [str(f) for f in files]


with gr.Blocks(title="Moses") as app:
    gr.Markdown("# Moses")
    gr.Markdown("AI-powered Gospel stem splitter using Demucs")

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

    run_button = gr.Button("Split Song")

    status = gr.Textbox(label="Status")
    outputs = gr.File(label="Separated Stems", file_count="multiple")

    run_button.click(
        split_song,
        inputs=[audio, model, mode],
        outputs=[status, outputs]
    )

app.launch()

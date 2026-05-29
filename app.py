import gradio as gr

from utils.async_processing import run_demucs_job
from utils.audio import check_ffmpeg
from utils.config import load_config
from utils.job_store import job_store
from utils.presets import EXPORT_PRESETS
from utils.system import detect_device
from utils.workers import background_worker
from utils.bootstrap import diagnostics_text

config = load_config()

device_info = detect_device()
ffmpeg_installed = check_ffmpeg()

MODEL_OPTIONS = {
    "Fast Processing (Lower Quality)": "htdemucs",
    "Studio Quality (Recommended)": "htdemucs_ft",
    "Musician Detail Separation": "htdemucs_6s",
}

MODEL_DESCRIPTIONS = {
    "Fast Processing (Lower Quality)": (
        "Best for quick rehearsals and slower computers. "
        "Faster processing with lower separation quality."
    ),
    "Studio Quality (Recommended)": (
        "Best overall quality for Gospel, worship, choir, and live music. "
        "Recommended for Ableton exports and rehearsals."
    ),
    "Musician Detail Separation": (
        "Separates additional musical elements like guitar and piano more aggressively. "
        "Useful for learning parts, but may create more audio artifacts."
    ),
}

X32_THEME_CSS = """
body {
    background: #0b0f14 !important;
}

.gradio-container {
    background: linear-gradient(to bottom, #11161d, #0b0f14) !important;
    color: #d7dde5 !important;
    font-family: 'Segoe UI', sans-serif;
}

h1, h2, h3, p, label {
    color: #d7dde5 !important;
}

.block {
    background: #161c24 !important;
    border: 1px solid #2a323d !important;
    border-radius: 10px !important;
    box-shadow: 0 0 12px rgba(0,0,0,0.35) !important;
}

button.primary {
    background: linear-gradient(to bottom, #00b3ff, #0077b6) !important;
    border: none !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 8px !important;
}

button.primary:hover {
    background: linear-gradient(to bottom, #27c1ff, #0096e6) !important;
}

textarea,
input,
select {
    background: #0f141a !important;
    color: #d7dde5 !important;
    border: 1px solid #2d3742 !important;
}

.tab-nav button {
    background: #151b22 !important;
    color: #d7dde5 !important;
    border: 1px solid #2a323d !important;
}

.tab-nav button.selected {
    background: #00a8ff !important;
    color: white !important;
}

.progress-text {
    color: #00d084 !important;
    font-weight: bold !important;
}
"""


def empty_job_outputs(message="No active job."):
    return (
        message,
        None,
        None,
        None,
        None,
        None,
        gr.update(value=0),
        gr.update(value="Idle")
    )


def normalize_outputs(outputs):
    if outputs is None:
        return {}

    if isinstance(outputs, dict):
        return outputs

    if isinstance(outputs, list):
        normalized = {
            "vocals": outputs[0] if len(outputs) > 0 else None,
            "drums": outputs[1] if len(outputs) > 1 else None,
            "bass": outputs[2] if len(outputs) > 2 else None,
            "other": outputs[3] if len(outputs) > 3 else None,
        }

        return normalized

    return {}


def queue_single_job(audio_file, model_key, export_preset):
    actual_model = MODEL_OPTIONS[model_key]

    job = job_store.create_job(
        audio_file,
        actual_model,
        "4 Stems",
        export_preset
    )

    background_worker.add_task(
        run_demucs_job,
        job.job_id,
        device_info["device"],
        config["slow_playback_rate"]
    )

    return job


def submit_job(audio_file, model_key, export_preset):
    if audio_file is None:
        return (
            "No file uploaded.",
            "",
            None,
            None,
            None,
            None,
            None,
            gr.update(value=0),
            gr.update(value="Idle")
        )

    if not ffmpeg_installed:
        return (
            "FFmpeg is not installed.",
            "",
            None,
            None,
            None,
            None,
            None,
            gr.update(value=0),
            gr.update(value="Error")
        )

    job = queue_single_job(audio_file, model_key, export_preset)

    return (
        f"Job submitted: {job.song_name}",
        job.job_id,
        None,
        None,
        None,
        None,
        None,
        gr.update(value=0),
        gr.update(value="Queued")
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

    outputs = normalize_outputs(job.outputs)

    vocals_file = outputs.get("vocals")
    drums_file = outputs.get("drums")
    bass_file = outputs.get("bass")
    other_file = outputs.get("other")

    return (
        status_text,
        vocals_file,
        drums_file,
        bass_file,
        other_file,
        job.zip_file,
        gr.update(value=job.progress),
        gr.update(value=job.status.title())
    )


def update_model_description(model_key):
    return MODEL_DESCRIPTIONS.get(model_key, "")


with gr.Blocks(title="Moses", css=X32_THEME_CSS) as demo:
    gr.Markdown("# Moses")
    gr.Markdown("### Gospel Stem Separation Console")

    with gr.Tab("Split Song"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Input Routing")

                audio_input = gr.Audio(
                    label="Stereo Input Track",
                    type="filepath"
                )

                model_choice = gr.Dropdown(
                    choices=list(MODEL_OPTIONS.keys()),
                    value="Studio Quality (Recommended)",
                    label="Separation Engine"
                )

                model_description = gr.Markdown(
                    MODEL_DESCRIPTIONS["Studio Quality (Recommended)"]
                )

                model_choice.change(
                    update_model_description,
                    inputs=[model_choice],
                    outputs=[model_description]
                )

                export_preset = gr.Dropdown(
                    choices=list(EXPORT_PRESETS.keys()),
                    value=list(EXPORT_PRESETS.keys())[0],
                    label="Output Routing Preset"
                )

                split_button = gr.Button(
                    "Process Stem Split",
                    variant="primary"
                )

                job_id_output = gr.Textbox(
                    label="Processing Job ID",
                    interactive=False
                )

            with gr.Column(scale=2):
                gr.Markdown("## Stem Output Matrix")

                status_output = gr.Textbox(
                    label="Engine Status"
                )

                progress_output = gr.Slider(
                    label="Processing Meter",
                    minimum=0,
                    maximum=100,
                    value=0,
                    interactive=False
                )

                vocals_output = gr.File(label="Vocals Bus")
                drums_output = gr.File(label="Drums Bus")
                bass_output = gr.File(label="Bass Bus")
                other_output = gr.File(label="Music Bus")
                zip_output = gr.File(label="Ableton Session Export")

        split_button.click(
            submit_job,
            inputs=[
                audio_input,
                model_choice,
                export_preset,
            ],
            outputs=[
                status_output,
                job_id_output,
                vocals_output,
                drums_output,
                bass_output,
                other_output,
                zip_output,
                progress_output,
                status_output,
            ]
        )

        polling_timer = gr.Timer(2)

        polling_timer.tick(
            poll_job,
            inputs=[job_id_output],
            outputs=[
                status_output,
                vocals_output,
                drums_output,
                bass_output,
                other_output,
                zip_output,
                progress_output,
                status_output,
            ]
        )

    with gr.Tab("Diagnostics"):
        diagnostics_box = gr.Textbox(
            value=diagnostics_text(),
            lines=20,
            label="System Diagnostics"
        )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
    )

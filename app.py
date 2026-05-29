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

GPU_STATUS = "CUDA ACTIVE" if device_info.get("cuda") else "CPU MODE"
GPU_NAME = device_info.get("name", "Unknown Device")

MODEL_OPTIONS = {
    "Fast Processing": "htdemucs",
    "Studio Quality": "htdemucs_ft",
    "Musician Detail": "htdemucs_6s",
}

MODEL_DESCRIPTIONS = {
    "Fast Processing": "Fastest separation with lower quality.",
    "Studio Quality": "Best quality for Gospel, worship, and rehearsal tracks.",
    "Musician Detail": "Extra instrument detail for learning parts.",
}

X32_THEME_CSS = """
body {
    background: #090d12 !important;
}

.gradio-container {
    max-width: 1600px !important;
    margin: auto !important;
    background: linear-gradient(to bottom, #10161d, #090d12) !important;
    color: #d8e0ea !important;
    font-family: 'Segoe UI', sans-serif;
    padding-top: 10px !important;
}

.audio-card {
    background: #111821;
    border: 1px solid #273240;
    border-radius: 8px;
    padding: 8px;
}

.status-strip {
    background: linear-gradient(to right, #0d141c, #121d28);
    border: 1px solid #273240;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 10px;
    font-size: 14px;
    font-weight: 600;
    color: #65d7ff;
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
        "",
    )


def normalize_outputs(outputs):
    if outputs is None:
        return {}

    if isinstance(outputs, dict):
        return outputs

    if isinstance(outputs, list):
        return {
            "vocals": outputs[0] if len(outputs) > 0 else None,
            "drums": outputs[1] if len(outputs) > 1 else None,
            "bass": outputs[2] if len(outputs) > 2 else None,
            "other": outputs[3] if len(outputs) > 3 else None,
        }

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
            None,
            None,
            None,
            None,
            None,
            gr.update(value=0),
            "",
        )

    job = queue_single_job(audio_file, model_key, export_preset)

    return (
        f"QUEUED • {job.song_name}",
        None,
        None,
        None,
        None,
        None,
        gr.update(value=0),
        job.job_id,
    )


def poll_job(job_id):
    if not job_id:
        return empty_job_outputs()

    job = job_store.get_job(job_id)

    if not job:
        return empty_job_outputs("Job not found.")

    outputs = normalize_outputs(job.outputs)

    return (
        f"{job.status.upper()} • {job.progress}% • {job.message}",
        outputs.get("vocals"),
        outputs.get("drums"),
        outputs.get("bass"),
        outputs.get("other"),
        job.zip_file,
        gr.update(value=job.progress),
        job.job_id,
    )


def update_model_description(model_key):
    return MODEL_DESCRIPTIONS.get(model_key, "")


with gr.Blocks(title="Moses") as demo:

    gr.HTML(
        f"""
        <div class='status-strip'>
        MOSES • {GPU_STATUS} • {GPU_NAME}
        </div>
        """
    )

    with gr.Tabs():

        with gr.Tab("Split Song"):

            with gr.Row():
                with gr.Column(scale=3):

                    audio_input = gr.Audio(
                        label="INPUT TRACK",
                        type="filepath",
                        height=180
                    )

                    with gr.Row():
                        model_choice = gr.Dropdown(
                            choices=list(MODEL_OPTIONS.keys()),
                            value="Studio Quality",
                            label="ENGINE"
                        )

                        export_preset = gr.Dropdown(
                            choices=list(EXPORT_PRESETS.keys()),
                            value=list(EXPORT_PRESETS.keys())[0],
                            label="PRESET"
                        )

                    model_description = gr.Markdown(
                        MODEL_DESCRIPTIONS["Studio Quality"]
                    )

                    model_choice.change(
                        update_model_description,
                        inputs=[model_choice],
                        outputs=[model_description]
                    )

                    split_button = gr.Button(
                        "PROCESS STEM SPLIT",
                        variant="primary"
                    )

                    engine_status = gr.Textbox(
                        label="ENGINE STATUS",
                        value="IDLE"
                    )

                    processing_meter = gr.Slider(
                        label="PROCESSING METER",
                        minimum=0,
                        maximum=100,
                        value=0,
                        interactive=False
                    )

                with gr.Column(scale=4):

                    with gr.Row():
                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### VOCALS")
                            vocals_stem = gr.Audio(
                                label="Preview + Download",
                                show_download_button=True,
                                interactive=False
                            )

                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### DRUMS")
                            drums_stem = gr.Audio(
                                label="Preview + Download",
                                show_download_button=True,
                                interactive=False
                            )

                    with gr.Row():
                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### BASS")
                            bass_stem = gr.Audio(
                                label="Preview + Download",
                                show_download_button=True,
                                interactive=False
                            )

                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### MUSIC")
                            other_stem = gr.Audio(
                                label="Preview + Download",
                                show_download_button=True,
                                interactive=False
                            )

                    zip_output = gr.File(label="ABLETON EXPORT PACKAGE")

            hidden_job_id = gr.Textbox(visible=False)

            split_button.click(
                submit_job,
                inputs=[
                    audio_input,
                    model_choice,
                    export_preset,
                ],
                outputs=[
                    engine_status,
                    vocals_stem,
                    drums_stem,
                    bass_stem,
                    other_stem,
                    zip_output,
                    processing_meter,
                    hidden_job_id,
                ]
            )

            polling_timer = gr.Timer(2)

            polling_timer.tick(
                poll_job,
                inputs=[hidden_job_id],
                outputs=[
                    engine_status,
                    vocals_stem,
                    drums_stem,
                    bass_stem,
                    other_stem,
                    zip_output,
                    processing_meter,
                    hidden_job_id,
                ]
            )

        with gr.Tab("Diagnostics"):
            gr.Textbox(
                value=diagnostics_text(),
                lines=18,
                label="SYSTEM DIAGNOSTICS"
            )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        css=X32_THEME_CSS,
    )

from pathlib import Path

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
:root {
    --bg: #05070b;
    --bg-soft: #0b0f17;
    --card: rgba(14, 20, 32, 0.8);
    --ink: #eef4ff;
    --muted: #97a7c2;
    --line: #1d2940;
    --accent: #8b5cf6;
    --accent-2: #2563eb;
    --accent-3: #22d3ee;
}

body {
    color: var(--ink) !important;
    background:
        radial-gradient(900px 500px at 85% -15%, rgba(139, 92, 246, .28), transparent 65%),
        radial-gradient(700px 420px at 8% 0%, rgba(37, 99, 235, .22), transparent 60%),
        linear-gradient(180deg, #05070b, #060912 50%, #05070b) !important;
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    color: var(--ink) !important;
    background: transparent !important;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    padding: 16px 18px 28px !important;
}

.block {
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.025)) !important;
    box-shadow: 0 18px 60px rgba(0,0,0,.38) !important;
}

.audio-card {
    background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 10px;
}

.status-strip {
    border: 1px solid var(--line);
    border-radius: 12px;
    background: rgba(7, 10, 16, 0.72);
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 30px rgba(0,0,0,.34);
    padding: 12px 14px;
    margin-bottom: 12px;
    font-weight: 700;
    letter-spacing: .02em;
    color: #dbe8ff;
}

button.primary {
    border: none !important;
    color: #f1f7ff !important;
    background: linear-gradient(120deg, var(--accent), var(--accent-2)) !important;
}

button.secondary {
    border: 1px solid #314565 !important;
    background: rgba(22, 30, 44, .75) !important;
    color: #d7e5ff !important;
}

footer {
    display: none !important;
}
"""


def empty_job_outputs(message="No active job."):
    return (
        message,
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        None,
        gr.update(value=0, interactive=False),
        gr.update(interactive=True, variant="primary"),
        "",
    )



def first_audio_file(value):
    if value is None:
        return None

    if isinstance(value, dict):
        candidate = value.get("path") or value.get("name")
        return str(candidate) if candidate else None

    if isinstance(value, list):
        return str(value[0]) if value else None

    return str(value)



def normalize_outputs(outputs):
    if outputs is None:
        return {}

    if isinstance(outputs, dict):
        return {
            "vocals": first_audio_file(outputs.get("vocals")),
            "drums": first_audio_file(outputs.get("drums")),
            "bass": first_audio_file(outputs.get("bass")),
            "other": first_audio_file(outputs.get("other")),
        }

    if isinstance(outputs, list):
        return {
            "drums": first_audio_file(outputs[0]) if len(outputs) > 0 else None,
            "bass": first_audio_file(outputs[1]) if len(outputs) > 1 else None,
            "other": first_audio_file(outputs[2]) if len(outputs) > 2 else None,
            "vocals": first_audio_file(outputs[3]) if len(outputs) > 3 else None,
        }

    return {}



def normalize_audio_input(audio_input):
    if audio_input is None:
        return None

    if isinstance(audio_input, dict):
        candidate = audio_input.get("path") or audio_input.get("name")
        return str(candidate) if candidate else None

    if isinstance(audio_input, (list, tuple)):
        return str(audio_input[0]) if audio_input else None

    return str(audio_input)


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
    normalized_audio = normalize_audio_input(audio_file)

    if not normalized_audio or not Path(normalized_audio).exists():
        return (
            "No valid file uploaded.",
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            None,
            gr.update(value=0, interactive=False),
            gr.update(interactive=True, variant="primary"),
            "",
        )

    job = queue_single_job(normalized_audio, model_key, export_preset)

    return (
        f"PROCESSING • {job.song_name}",
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        None,
        gr.update(value=0, interactive=False),
        gr.update(interactive=False, variant="secondary"),
        job.job_id,
    )



def poll_job(job_id):
    if not job_id:
        return empty_job_outputs()

    job = job_store.get_job(job_id)

    if not job:
        return empty_job_outputs("Job not found.")

    outputs = normalize_outputs(job.outputs)

    processing_complete = job.status.lower() in ["complete", "completed", "finished"]

    return (
        f"{job.status.upper()} • {job.progress}% • {job.message}",
        gr.update(value=outputs.get("vocals")),
        gr.update(value=outputs.get("drums")),
        gr.update(value=outputs.get("bass")),
        gr.update(value=outputs.get("other")),
        job.zip_file,
        gr.update(value=job.progress, interactive=False),
        gr.update(
            interactive=processing_complete,
            variant="primary" if processing_complete else "secondary"
        ),
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
                        type="filepath"
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
                                label="Preview",
                                interactive=False,
                                type="filepath"
                            )

                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### DRUMS")
                            drums_stem = gr.Audio(
                                label="Preview",
                                interactive=False,
                                type="filepath"
                            )

                    with gr.Row():
                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### BASS")
                            bass_stem = gr.Audio(
                                label="Preview",
                                interactive=False,
                                type="filepath"
                            )

                        with gr.Column(elem_classes=["audio-card"]):
                            gr.Markdown("### MUSIC")
                            other_stem = gr.Audio(
                                label="Preview",
                                interactive=False,
                                type="filepath"
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
                    split_button,
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
                    split_button,
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

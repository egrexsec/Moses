from pathlib import Path
from datetime import datetime

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
    "Fast": "htdemucs",
    "Studio": "htdemucs_ft",
    "Detail": "htdemucs_6s",
}

MODEL_DESCRIPTIONS = {
    "Fast": "Fastest separation with lower quality.",
    "Studio": "Best quality for worship and rehearsal tracks.",
    "Detail": "Maximum instrument detail for practicing parts.",
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
}
body {
    color: var(--ink) !important;
    background:
        radial-gradient(900px 500px at 85% -15%, rgba(139, 92, 246, .28), transparent 65%),
        radial-gradient(700px 420px at 8% 0%, rgba(37, 99, 235, .22), transparent 60%),
        linear-gradient(180deg, #05070b, #060912 50%, #05070b) !important;
}
.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    color: var(--ink) !important;
    background: transparent !important;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    padding: 18px !important;
}
.block {
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.025)) !important;
    box-shadow: 0 18px 60px rgba(0,0,0,.38) !important;
}
.status-strip {
    border: 1px solid var(--line);
    border-radius: 12px;
    background: rgba(7, 10, 16, 0.72);
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 30px rgba(0,0,0,.34);
    padding: 12px 14px;
    margin-bottom: 14px;
    font-weight: 700;
    color: #dbe8ff;
}
.step-title { margin: 0 0 6px 0; font-weight: 700; font-size: 1.03rem; }
.step-sub { margin: 0 0 10px 0; color: #9fb0d0; font-size: .92rem; }
.card-title { margin: 0; font-size: .95rem; color: #d6e6ff; letter-spacing: .02em; }
.meta { color: #9fb0d0; font-size: .88rem; }
.audio-card {
    background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 10px;
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
footer { display: none !important; }
"""


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


def queue_snapshot():
    with job_store.lock:
        jobs = sorted(job_store.jobs.values(), key=lambda j: j.created_at, reverse=True)
    if not jobs:
        return "No jobs yet."
    lines = []
    for job in jobs[:4]:
        lines.append(f"- `{job.song_name}` · **{job.status.upper()}** · {job.progress}%")
    return "\n".join(lines)


def status_card(job):
    elapsed = max(0, int(datetime.now().timestamp() - job.created_at))
    return (
        f"<div><p class='card-title'>{job.song_name}</p>"
        f"<p class='meta'>Status: <b>{job.status.upper()}</b> · Progress: {job.progress}% · Elapsed: {elapsed}s</p>"
        f"<p class='meta'>{job.message}</p></div>"
    )


def empty_job_outputs(message="No active job."):
    return (
        f"<div><p class='card-title'>Idle</p><p class='meta'>{message}</p></div>",
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        None,
        gr.update(value=0, interactive=False),
        gr.update(interactive=True, variant="primary"),
        "",
        queue_snapshot(),
    )


def queue_single_job(audio_file, model_key, export_preset):
    actual_model = MODEL_OPTIONS[model_key]
    job = job_store.create_job(audio_file, actual_model, "4 Stems", export_preset)
    background_worker.add_task(
        run_demucs_job,
        job.job_id,
        device_info["device"],
        config["slow_playback_rate"],
    )
    return job


def submit_job(audio_file, model_key, export_preset):
    normalized_audio = normalize_audio_input(audio_file)
    if not normalized_audio or not Path(normalized_audio).exists():
        return (
            "<div><p class='card-title'>Upload required</p><p class='meta'>Select a valid audio file first.</p></div>",
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            None,
            gr.update(value=0, interactive=False),
            gr.update(interactive=True, variant="primary"),
            "",
            queue_snapshot(),
        )

    job = queue_single_job(normalized_audio, model_key, export_preset)
    return (
        status_card(job),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        None,
        gr.update(value=0, interactive=False),
        gr.update(interactive=False, variant="secondary"),
        job.job_id,
        queue_snapshot(),
    )


def poll_job(job_id):
    if not job_id:
        return empty_job_outputs()
    job = job_store.get_job(job_id)
    if not job:
        return empty_job_outputs("Job not found.")

    outputs = normalize_outputs(job.outputs)
    processing_complete = job.status.lower() in ["complete", "completed", "finished", "failed", "cancelled"]

    return (
        status_card(job),
        gr.update(value=outputs.get("vocals")),
        gr.update(value=outputs.get("drums")),
        gr.update(value=outputs.get("bass")),
        gr.update(value=outputs.get("other")),
        job.zip_file,
        gr.update(value=job.progress, interactive=False),
        gr.update(interactive=processing_complete, variant="primary" if processing_complete else "secondary"),
        job.job_id,
        queue_snapshot(),
    )


def update_model_description(model_key):
    return MODEL_DESCRIPTIONS.get(model_key, "")


with gr.Blocks(title="Moses") as demo:
    gr.HTML(
        f"""
        <div class='status-strip'>
        MOSES • {GPU_STATUS} • {GPU_NAME} • FFMPEG: {'OK' if ffmpeg_installed else 'MISSING'}
        </div>
        """
    )

    gr.Markdown("## Clean Stem Split Workflow")

    with gr.Row():
        with gr.Column(scale=3):
            gr.HTML("<p class='step-title'>Step 1 — Upload Track</p><p class='step-sub'>Use WAV/FLAC/ALAC (MP3 320 kbps acceptable).</p>")
            audio_input = gr.Audio(label="Input Track", type="filepath")

            gr.HTML("<p class='step-title'>Step 2 — Choose Quality</p><p class='step-sub'>Start with Studio for best balance.</p>")
            model_choice = gr.Radio(
                choices=list(MODEL_OPTIONS.keys()),
                value="Studio",
                label="Quality Preset",
            )
            model_description = gr.Markdown(MODEL_DESCRIPTIONS["Studio"])
            model_choice.change(update_model_description, inputs=[model_choice], outputs=[model_description])

            with gr.Accordion("Advanced", open=False):
                export_preset = gr.Dropdown(
                    choices=list(EXPORT_PRESETS.keys()),
                    value=list(EXPORT_PRESETS.keys())[0],
                    label="Export Preset",
                )
                gr.Markdown("Diagnostics")
                gr.Textbox(value=diagnostics_text(), lines=10, label="System")

            gr.HTML("<p class='step-title'>Step 3 — Start Split</p>")
            split_button = gr.Button("Split Stems", variant="primary")
            processing_meter = gr.Slider(label="Progress", minimum=0, maximum=100, value=0, interactive=False)

            gr.Markdown("### Queue")
            queue_md = gr.Markdown(value=queue_snapshot())

        with gr.Column(scale=4):
            gr.Markdown("### Job")
            job_status = gr.HTML("<div><p class='card-title'>Idle</p><p class='meta'>Upload a track to begin.</p></div>")

            gr.Markdown("### Results")
            with gr.Row():
                with gr.Column(elem_classes=["audio-card"]):
                    gr.Markdown("#### Vocals")
                    vocals_stem = gr.Audio(label="Preview", interactive=False, type="filepath")
                with gr.Column(elem_classes=["audio-card"]):
                    gr.Markdown("#### Drums")
                    drums_stem = gr.Audio(label="Preview", interactive=False, type="filepath")
            with gr.Row():
                with gr.Column(elem_classes=["audio-card"]):
                    gr.Markdown("#### Bass")
                    bass_stem = gr.Audio(label="Preview", interactive=False, type="filepath")
                with gr.Column(elem_classes=["audio-card"]):
                    gr.Markdown("#### Music")
                    other_stem = gr.Audio(label="Preview", interactive=False, type="filepath")

            zip_output = gr.File(label="Download ZIP")

    hidden_job_id = gr.Textbox(visible=False)

    split_button.click(
        submit_job,
        inputs=[audio_input, model_choice, export_preset],
        outputs=[
            job_status,
            vocals_stem,
            drums_stem,
            bass_stem,
            other_stem,
            zip_output,
            processing_meter,
            split_button,
            hidden_job_id,
            queue_md,
        ],
    )

    polling_timer = gr.Timer(2)
    polling_timer.tick(
        poll_job,
        inputs=[hidden_job_id],
        outputs=[
            job_status,
            vocals_stem,
            drums_stem,
            bass_stem,
            other_stem,
            zip_output,
            processing_meter,
            split_button,
            hidden_job_id,
            queue_md,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        css=X32_THEME_CSS,
    )

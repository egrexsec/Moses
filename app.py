import gradio as gr

from utils.async_processing import run_demucs_job
from utils.config import load_config
from utils.job_store import job_store
from utils.mixer import mix_stems
from utils.presets import EXPORT_PRESETS
from utils.system import detect_device
from utils.audio import check_ffmpeg
from utils.stems import categorize_stems
from utils.workers import background_worker

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


def submit_job(audio_file, model, mode, export_preset):
    if audio_file is None:
        return "No file uploaded.", ""

    if not ffmpeg_installed:
        return "FFmpeg is not installed.", ""

    job = job_store.create_job(
        audio_file,
        model,
        mode,
        export_preset
    )

    background_worker.add_task(
        run_demucs_job,
        job.job_id,
        device_info["device"],
        config["slow_playback_rate"]
    )

    return (
        f"Job submitted: {job.song_name}",
        job.job_id
    )


def poll_job(job_id):
    if not job_id:
        return (
            "No active job.",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        )

    job = job_store.get_job(job_id)

    if not job:
        return (
            "Job not found.",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        )

    status_text = (
        f"Status: {job.status} | "
        f"Progress: {job.progress}% | "
        f"Message: {job.message}"
    )

    queue_summary = job_store.summary()

    queue_text = (
        f"Queued: {queue_summary['queued']} | "
        f"Running: {queue_summary['running']} | "
        f"Complete: {queue_summary['complete']} | "
        f"Failed: {queue_summary['failed']}"
    )

    return (
        status_text,
        job.outputs,
        job.metadata,
        job.zip_file,
        job.practice_track,
        job.vocal_preview,
        job.waveform_image,
        getattr(job, "spectrogram_image", None),
        queue_text,
        job.band_mix
    )


def remix_stems(
    stem_files,
    vocals_gain,
    bass_gain,
    drums_gain,
    other_gain,
    mute_vocals,
    mute_bass,
    mute_drums,
    mute_other
):
    if not stem_files:
        return None

    gains = {
        "vocals": vocals_gain,
        "bass": bass_gain,
        "drums": drums_gain,
        "other": other_gain,
    }

    mutes = {
        "vocals": mute_vocals,
        "bass": mute_bass,
        "drums": mute_drums,
        "other": mute_other,
    }

    output_path = "mixes/custom_mix.wav"

    return mix_stems(
        stem_files,
        output_path,
        gains=gains,
        mutes=mutes
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

    with gr.Tab("Stem Separation"):
        audio = gr.Audio(type="filepath", label="Upload Song")

        submit_button = gr.Button("Submit Job")
        poll_button = gr.Button("Refresh Status")

        job_status = gr.Textbox(label="Job Status")
        job_id = gr.Textbox(label="Job ID")

        outputs = gr.File(label="Separated Stems", file_count="multiple")
        metadata = gr.Textbox(label="Song Information")
        zip_download = gr.File(label="Download ZIP")
        practice_track = gr.File(label="Slow Practice Track")
        vocal_preview = gr.Audio(label="Vocal Preview")
        waveform_preview = gr.Image(label="Waveform Preview")
        spectrogram_preview = gr.Image(label="Spectrogram Preview")
        queue_status = gr.Textbox(label="Queue Status")
        band_mix_preview = gr.Audio(label="Band Mix Preview")

        submit_button.click(
            submit_job,
            inputs=[audio, model, mode, export_preset],
            outputs=[job_status, job_id]
        )

        poll_button.click(
            poll_job,
            inputs=[job_id],
            outputs=[
                job_status,
                outputs,
                metadata,
                zip_download,
                practice_track,
                vocal_preview,
                waveform_preview,
                spectrogram_preview,
                queue_status,
                band_mix_preview
            ]
        )

    with gr.Tab("Mixer"):
        mixer_files = gr.File(
            label="Stem Files",
            file_count="multiple"
        )

        vocals_gain = gr.Slider(0, 2, value=1, label="Vocals Gain")
        bass_gain = gr.Slider(0, 2, value=1, label="Bass Gain")
        drums_gain = gr.Slider(0, 2, value=1, label="Drums Gain")
        other_gain = gr.Slider(0, 2, value=1, label="Other Gain")

        mute_vocals = gr.Checkbox(label="Mute Vocals")
        mute_bass = gr.Checkbox(label="Mute Bass")
        mute_drums = gr.Checkbox(label="Mute Drums")
        mute_other = gr.Checkbox(label="Mute Other")

        remix_button = gr.Button("Create Custom Mix")

        remix_output = gr.Audio(label="Custom Mix")

        remix_button.click(
            remix_stems,
            inputs=[
                mixer_files,
                vocals_gain,
                bass_gain,
                drums_gain,
                other_gain,
                mute_vocals,
                mute_bass,
                mute_drums,
                mute_other
            ],
            outputs=[remix_output]
        )

app.launch()

import gradio as gr

from utils.timeline import (
    add_loop,
    add_marker,
    analyze_audio_for_timeline,
    save_timeline,
    timeline_summary,
)
from utils.waveform_timeline import (
    generate_region_waveform,
    generate_timeline_waveform,
)

CURRENT = {
    "timeline": None,
    "audio": None,
}


def create_workspace(audio_file, title):
    if not audio_file:
        return "No audio uploaded.", None, None

    session = analyze_audio_for_timeline(audio_file, title)
    timeline_path = save_timeline(session)

    CURRENT["timeline"] = timeline_path
    CURRENT["audio"] = audio_file

    waveform = generate_timeline_waveform(timeline_path)

    return timeline_summary(timeline_path), timeline_path, waveform



def add_marker_ui(name, seconds, notes):
    timeline_path = CURRENT["timeline"]

    if not timeline_path:
        return "No timeline loaded.", None

    add_marker(timeline_path, name, seconds, notes)

    waveform = generate_timeline_waveform(timeline_path)

    return timeline_summary(timeline_path), waveform



def add_loop_ui(name, start_seconds, end_seconds, notes):
    timeline_path = CURRENT["timeline"]

    if not timeline_path:
        return "No timeline loaded.", None

    add_loop(
        timeline_path,
        name,
        start_seconds,
        end_seconds,
        notes,
    )

    waveform = generate_timeline_waveform(timeline_path)

    return timeline_summary(timeline_path), waveform



def preview_region(start_seconds, end_seconds):
    audio_file = CURRENT["audio"]

    if not audio_file:
        return None

    return generate_region_waveform(
        audio_file,
        start_seconds,
        end_seconds,
    )


with gr.Blocks(title="Moses Waveform Workspace") as app:
    gr.Markdown("# Moses Waveform Timeline")
    gr.Markdown("Visual rehearsal timeline with markers and loop regions.")

    with gr.Tab("Timeline"):
        audio = gr.Audio(type="filepath", label="Upload Audio")
        title = gr.Textbox(label="Timeline Title")

        create_button = gr.Button("Create Timeline")

        summary = gr.Textbox(label="Timeline Summary", lines=18)
        timeline_file = gr.Textbox(label="Timeline File")
        waveform_image = gr.Image(label="Waveform Timeline")

        create_button.click(
            create_workspace,
            inputs=[audio, title],
            outputs=[summary, timeline_file, waveform_image]
        )

    with gr.Tab("Markers"):
        marker_name = gr.Textbox(label="Marker Name")
        marker_time = gr.Number(label="Time (seconds)")
        marker_notes = gr.Textbox(label="Marker Notes")

        marker_button = gr.Button("Add Marker")

        marker_button.click(
            add_marker_ui,
            inputs=[marker_name, marker_time, marker_notes],
            outputs=[summary, waveform_image]
        )

    with gr.Tab("Loops"):
        loop_name = gr.Textbox(label="Loop Name")
        loop_start = gr.Number(label="Loop Start")
        loop_end = gr.Number(label="Loop End")
        loop_notes = gr.Textbox(label="Loop Notes")

        loop_button = gr.Button("Add Loop")

        loop_button.click(
            add_loop_ui,
            inputs=[loop_name, loop_start, loop_end, loop_notes],
            outputs=[summary, waveform_image]
        )

    with gr.Tab("Region Preview"):
        region_start = gr.Number(label="Preview Start")
        region_end = gr.Number(label="Preview End")

        region_button = gr.Button("Generate Region Waveform")
        region_image = gr.Image(label="Region Waveform")

        region_button.click(
            preview_region,
            inputs=[region_start, region_end],
            outputs=[region_image]
        )

app.launch()

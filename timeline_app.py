import gradio as gr

from utils.timeline import (
    add_loop,
    add_marker,
    analyze_audio_for_timeline,
    export_loop_region,
    save_timeline,
    timeline_summary,
)


current_timeline_path = {
    "path": None,
    "audio": None,
}



def create_timeline(audio_file, title):
    if not audio_file:
        return "No audio uploaded.", None

    session = analyze_audio_for_timeline(audio_file, title)
    path = save_timeline(session)

    current_timeline_path["path"] = path
    current_timeline_path["audio"] = audio_file

    return timeline_summary(path), path



def create_marker(name, time_seconds, notes):
    path = current_timeline_path["path"]

    if not path:
        return "No timeline loaded."

    add_marker(path, name, time_seconds, notes)

    return timeline_summary(path)



def create_loop(name, start_seconds, end_seconds, notes):
    path = current_timeline_path["path"]

    if not path:
        return "No timeline loaded."

    add_loop(path, name, start_seconds, end_seconds, notes)

    return timeline_summary(path)



def export_loop(start_seconds, end_seconds):
    audio_file = current_timeline_path["audio"]

    if not audio_file:
        return None

    output = "exports/timeline_loop.wav"

    return export_loop_region(
        audio_file,
        start_seconds,
        end_seconds,
        output,
    )


with gr.Blocks(title="Moses Timeline") as app:
    gr.Markdown("# Moses Timeline Playback Workspace")
    gr.Markdown("Loop regions, rehearsal markers, and timeline planning.")

    with gr.Tab("Timeline"):
        audio = gr.Audio(type="filepath", label="Upload Audio")
        timeline_title = gr.Textbox(label="Timeline Title")

        create_button = gr.Button("Create Timeline")

        timeline_output = gr.Textbox(
            label="Timeline Summary",
            lines=20
        )

        timeline_path = gr.Textbox(label="Timeline File")

        create_button.click(
            create_timeline,
            inputs=[audio, timeline_title],
            outputs=[timeline_output, timeline_path]
        )

    with gr.Tab("Markers"):
        marker_name = gr.Textbox(label="Marker Name")
        marker_time = gr.Number(label="Time (seconds)")
        marker_notes = gr.Textbox(label="Notes")

        marker_button = gr.Button("Add Marker")

        marker_button.click(
            create_marker,
            inputs=[marker_name, marker_time, marker_notes],
            outputs=[timeline_output]
        )

    with gr.Tab("Loop Regions"):
        loop_name = gr.Textbox(label="Loop Name")
        loop_start = gr.Number(label="Loop Start")
        loop_end = gr.Number(label="Loop End")
        loop_notes = gr.Textbox(label="Loop Notes")

        loop_button = gr.Button("Add Loop")

        loop_button.click(
            create_loop,
            inputs=[loop_name, loop_start, loop_end, loop_notes],
            outputs=[timeline_output]
        )

    with gr.Tab("Loop Export"):
        export_start = gr.Number(label="Export Start")
        export_end = gr.Number(label="Export End")

        export_button = gr.Button("Export Loop Region")
        export_output = gr.File(label="Exported Region")

        export_button.click(
            export_loop,
            inputs=[export_start, export_end],
            outputs=[export_output]
        )

app.launch()

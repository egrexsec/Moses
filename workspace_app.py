import gradio as gr

from utils.workspace_ui import (
    add_song_to_project,
    create_workspace_project,
    project_detail_text,
    projects_dataframe,
)


def refresh_and_clear():
    return projects_dataframe()


with gr.Blocks(title="Moses Workspace") as app:
    gr.Markdown("# Moses Workspace")
    gr.Markdown("Persistent project and rehearsal workspace for Moses.")

    with gr.Tab("Projects"):
        with gr.Row():
            with gr.Column():
                project_name = gr.Textbox(label="Project Name")
                project_description = gr.Textbox(label="Description")
                project_type = gr.Dropdown(
                    choices=[
                        "rehearsal",
                        "sunday_service",
                        "choir",
                        "stem_cleanup",
                        "transcription"
                    ],
                    value="rehearsal",
                    label="Project Type"
                )

                create_project_button = gr.Button("Create Project")
                create_project_status = gr.Textbox(label="Status")
                active_project_id = gr.Textbox(label="Active Project ID")

            with gr.Column():
                projects_table = gr.Dataframe(
                    label="Project Browser",
                    interactive=False
                )
                refresh_projects_button = gr.Button("Refresh Projects")

        create_project_button.click(
            create_workspace_project,
            inputs=[project_name, project_description, project_type],
            outputs=[create_project_status, active_project_id]
        )

        refresh_projects_button.click(
            refresh_and_clear,
            outputs=[projects_table]
        )

    with gr.Tab("Setlist"):
        gr.Markdown("## Add Song to Project")

        song_title = gr.Textbox(label="Song Title")
        song_source_path = gr.Textbox(label="Source Path")
        song_order = gr.Number(label="Song Order", value=0, precision=0)
        song_notes = gr.Textbox(label="Notes")

        add_song_button = gr.Button("Add Song")
        add_song_status = gr.Textbox(label="Status")

        add_song_button.click(
            add_song_to_project,
            inputs=[
                active_project_id,
                song_title,
                song_source_path,
                song_notes,
                song_order
            ],
            outputs=[add_song_status]
        )

    with gr.Tab("Project Details"):
        load_project_button = gr.Button("Load Active Project")
        project_details = gr.Textbox(
            label="Project Details",
            lines=18
        )

        load_project_button.click(
            project_detail_text,
            inputs=[active_project_id],
            outputs=[project_details]
        )


app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    show_error=True,
)

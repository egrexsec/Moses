import gradio as gr

from utils.runtime_diagnostics import (
    active_processes_text,
    bootstrap_dataframe,
    diagnostics_report_text,
    gpu_status_text,
    recent_jobs_dataframe,
    system_runtime_text,
    worker_status_text,
)

with gr.Blocks(title="Moses Diagnostics") as app:
    gr.Markdown("# Moses Runtime Diagnostics")
    gr.Markdown("Live operational diagnostics for the Moses processing platform.")

    refresh_button = gr.Button("Refresh Diagnostics")

    with gr.Tab("Bootstrap"):
        bootstrap_table = gr.Dataframe(
            label="Startup Validation",
            interactive=False
        )

    with gr.Tab("Runtime"):
        runtime_text = gr.Textbox(
            label="System Runtime",
            lines=12
        )

    with gr.Tab("GPU Scheduler"):
        gpu_text = gr.Textbox(
            label="GPU Scheduler Status",
            lines=14
        )

    with gr.Tab("Worker Pools"):
        worker_text = gr.Textbox(
            label="Worker Pool Status",
            lines=12
        )

    with gr.Tab("Active Processes"):
        process_text = gr.Textbox(
            label="Active Process Registry",
            lines=12
        )

    with gr.Tab("Recent Jobs"):
        jobs_table = gr.Dataframe(
            label="Recent Jobs",
            interactive=False
        )

    with gr.Tab("Combined Report"):
        report_text = gr.Textbox(
            label="Diagnostics Report",
            lines=30
        )

    refresh_button.click(
        fn=lambda: (
            bootstrap_dataframe(),
            system_runtime_text(),
            gpu_status_text(),
            worker_status_text(),
            active_processes_text(),
            recent_jobs_dataframe(),
            diagnostics_report_text(),
        ),
        outputs=[
            bootstrap_table,
            runtime_text,
            gpu_text,
            worker_text,
            process_text,
            jobs_table,
            report_text,
        ]
    )

app.launch()

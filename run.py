from utils.bootstrap import diagnostics_text, write_diagnostics_report


print(diagnostics_text())
write_diagnostics_report()


APP_STARTED = False


try:
    import app

    if hasattr(app, "demo"):
        print("Launching Moses main application...")
        app.demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True,
        )
        APP_STARTED = True

except Exception as exc:
    print(f"Failed to launch main app: {exc}")


if not APP_STARTED:
    print("Trying workspace app fallback...")

    import workspace_app

    if hasattr(workspace_app, "app"):
        workspace_app.app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True,
        )

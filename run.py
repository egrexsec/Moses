import traceback

from utils.bootstrap import diagnostics_text, write_diagnostics_report


print(diagnostics_text())
write_diagnostics_report()


try:
    import app

    if hasattr(app, "demo"):
        print("Launching Moses main application...")

        app.demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True,
        )

    else:
        raise RuntimeError("Main app loaded but no Gradio demo object was found.")

except Exception as exc:
    print("\nFailed to launch Moses main application.\n")
    print(str(exc))
    print("\nFull traceback:\n")
    traceback.print_exc()

    raise SystemExit(1)

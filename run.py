from utils.bootstrap import diagnostics_text, write_diagnostics_report


print(diagnostics_text())
write_diagnostics_report()

try:
    import app
except Exception as exc:
    print(f"Failed to launch main app: {exc}")
    print("Trying workspace app fallback...")
    import workspace_app

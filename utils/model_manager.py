from pathlib import Path
import subprocess
import sys

MODEL_CACHE_DIR = Path("models")

SUPPORTED_MODELS = {
    "htdemucs": {
        "description": "Standard Demucs model"
    },
    "htdemucs_ft": {
        "description": "Fine tuned Demucs model"
    },
    "htdemucs_6s": {
        "description": "6 stem Demucs model"
    },
}


def ensure_model_directory():
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def model_exists(model_name):
    ensure_model_directory()

    matches = list(MODEL_CACHE_DIR.glob(f"*{model_name}*"))
    return len(matches) > 0



def download_model(model_name):
    if model_name not in SUPPORTED_MODELS:
        return False, f"Unsupported model: {model_name}"

    ensure_model_directory()

    if model_exists(model_name):
        return True, f"Model already cached: {model_name}"

    try:
        command = [
            sys.executable,
            "-m",
            "demucs",
            "--name",
            model_name,
            "--help"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return True, f"Model prepared: {model_name}"

        return False, result.stderr[:500]

    except Exception as exc:
        return False, str(exc)



def ensure_required_models(models=None):
    if models is None:
        models = list(SUPPORTED_MODELS.keys())

    results = []

    for model_name in models:
        success, message = download_model(model_name)

        results.append({
            "model": model_name,
            "success": success,
            "message": message,
        })

    return results



def models_summary_text():
    ensure_model_directory()

    lines = ["Demucs Model Cache", ""]

    for model_name in SUPPORTED_MODELS:
        exists = model_exists(model_name)
        status = "READY" if exists else "MISSING"

        lines.append(f"[{status}] {model_name}")

    return "\n".join(lines)

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from utils.config import DEFAULT_CONFIG, CONFIG_PATH, load_config, save_config
from utils.database import init_db


REQUIRED_DIRECTORIES = [
    "exports",
    "mixes",
    "workspaces",
    "cache",
    "models",
    "logs",
    "temp",
    "separated",
    "spectrograms",
]


REQUIRED_COMMANDS = [
    "ffmpeg",
    "ffprobe",
]


DEMUX_MODELS = [
    "htdemucs",
    "htdemucs_ft",
    "htdemucs_6s",
]


def check_python_version():
    major, minor = sys.version_info[:2]

    return {
        "name": "Python",
        "ok": major == 3 and minor >= 10,
        "details": f"Python {major}.{minor}",
        "fix": "Install Python 3.10 or newer."
    }


def check_command(command):
    path = shutil.which(command)

    return {
        "name": command,
        "ok": path is not None,
        "details": path or "Not found in PATH",
        "fix": f"Install {command} and ensure it is available in PATH."
    }


def check_torch_cuda():
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else "CPU only"

        return {
            "name": "PyTorch CUDA",
            "ok": True,
            "details": f"CUDA available: {cuda_available} | Device: {gpu_name}",
            "fix": "Install a CUDA-enabled PyTorch build if GPU acceleration is needed."
        }
    except Exception as exc:
        return {
            "name": "PyTorch CUDA",
            "ok": False,
            "details": str(exc),
            "fix": "Install torch and torchaudio from the PyTorch install guide."
        }


def check_demucs():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "demucs", "--help"],
            capture_output=True,
            text=True,
            timeout=20,
        )

        return {
            "name": "Demucs",
            "ok": result.returncode == 0,
            "details": "Demucs command available" if result.returncode == 0 else result.stderr[:300],
            "fix": "Install Demucs with: pip install demucs"
        }
    except Exception as exc:
        return {
            "name": "Demucs",
            "ok": False,
            "details": str(exc),
            "fix": "Install Demucs with: pip install demucs"
        }


def ensure_directories():
    created = []

    for directory in REQUIRED_DIRECTORIES:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(directory)

    return {
        "name": "Directories",
        "ok": True,
        "details": f"Created: {', '.join(created)}" if created else "All required directories exist",
        "fix": "Ensure the application has write permission in the project directory."
    }


def ensure_config():
    try:
        if not CONFIG_PATH.exists():
            save_config(DEFAULT_CONFIG)
            details = "Created default config.json"
        else:
            config = load_config()
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            save_config(merged)
            details = "Config loaded and self-healed"

        return {
            "name": "Config",
            "ok": True,
            "details": details,
            "fix": "Delete config.json and restart Moses to regenerate defaults."
        }
    except Exception as exc:
        return {
            "name": "Config",
            "ok": False,
            "details": str(exc),
            "fix": "Check config.json syntax or delete it to regenerate."
        }


def ensure_database():
    try:
        init_db()

        return {
            "name": "SQLite Database",
            "ok": True,
            "details": "moses.db initialized",
            "fix": "Ensure write permission in the Moses project directory."
        }
    except Exception as exc:
        return {
            "name": "SQLite Database",
            "ok": False,
            "details": str(exc),
            "fix": "Check filesystem permissions and database lock state."
        }


def check_nvidia_smi():
    path = shutil.which("nvidia-smi")

    if not path:
        return {
            "name": "NVIDIA Driver",
            "ok": False,
            "details": "nvidia-smi not found",
            "fix": "Install NVIDIA drivers if GPU acceleration is required."
        }

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return {
            "name": "NVIDIA Driver",
            "ok": result.returncode == 0,
            "details": result.stdout.strip() or result.stderr.strip(),
            "fix": "Install or repair NVIDIA drivers."
        }
    except Exception as exc:
        return {
            "name": "NVIDIA Driver",
            "ok": False,
            "details": str(exc),
            "fix": "Install or repair NVIDIA drivers."
        }


def run_bootstrap_checks():
    checks = [
        check_python_version(),
        ensure_directories(),
        ensure_config(),
        ensure_database(),
    ]

    for command in REQUIRED_COMMANDS:
        checks.append(check_command(command))

    checks.append(check_demucs())
    checks.append(check_torch_cuda())
    checks.append(check_nvidia_smi())

    return checks


def diagnostics_text():
    checks = run_bootstrap_checks()
    lines = ["Moses Startup Diagnostics", ""]

    for check in checks:
        status = "PASS" if check["ok"] else "WARN"
        lines.append(f"[{status}] {check['name']}: {check['details']}")
        if not check["ok"]:
            lines.append(f"  Fix: {check['fix']}")

    return "\n".join(lines)


def write_diagnostics_report(path="logs/startup_diagnostics.json"):
    checks = run_bootstrap_checks()
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(checks, f, indent=4)

    return str(output_path)


if __name__ == "__main__":
    print(diagnostics_text())
    write_diagnostics_report()

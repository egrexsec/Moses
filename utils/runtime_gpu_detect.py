import json
import shutil
import subprocess
from pathlib import Path


def run_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            return True, result.stdout.strip()

        return False, result.stderr.strip()

    except Exception as exc:
        return False, str(exc)


class RuntimeGPUDetector:
    def __init__(self):
        self.results = {
            "gpu_available": False,
            "nvidia_smi": False,
            "docker_gpu_runtime": False,
            "cuda_visible": False,
            "recommended_runtime": "cpu",
            "gpu_name": None,
        }

    def detect_nvidia_smi(self):
        exists = shutil.which("nvidia-smi") is not None
        self.results["nvidia_smi"] = exists

        if not exists:
            return

        success, output = run_command([
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        ])

        if success:
            gpu_name = output.splitlines()[0].strip()
            self.results["gpu_name"] = gpu_name
            self.results["gpu_available"] = True

    def detect_docker_gpu_runtime(self):
        success, output = run_command([
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            "nvidia/cuda:12.1.0-runtime-ubuntu22.04",
            "nvidia-smi",
        ])

        self.results["docker_gpu_runtime"] = success

        if success:
            self.results["cuda_visible"] = True
            self.results["recommended_runtime"] = "gpu"

    def run(self):
        self.detect_nvidia_smi()

        if self.results["gpu_available"]:
            self.detect_docker_gpu_runtime()

        return self.results


if __name__ == "__main__":
    detector = RuntimeGPUDetector()
    results = detector.run()

    Path("logs").mkdir(exist_ok=True)

    with open("logs/runtime_gpu_detection.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print("Moses Runtime GPU Detection")
    print()

    for key, value in results.items():
        print(f"{key}: {value}")

    print()

    if results["recommended_runtime"] == "gpu":
        print("Recommended Startup:")
        print("docker compose up --build")
    else:
        print("Recommended Startup:")
        print("docker compose -f docker/docker-compose.cpu.yml up --build")

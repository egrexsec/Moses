from pathlib import Path
import json


CONFIG_PATH = Path("config.json")


DEFAULT_CONFIG = {
    "default_model": "htdemucs",
    "default_mode": "4 Stems",
    "slow_playback_rate": 0.75,
    "export_directory": "exports",
    "worker_pool_size": 2,
    "max_gpu_jobs": 1
}


def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)

    return merged_config


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

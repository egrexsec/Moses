from pathlib import Path
import json


CONFIG_PATH = Path("config.json")


DEFAULT_CONFIG = {
    "default_model": "htdemucs",
    "default_mode": "4 Stems",
    "slow_playback_rate": 0.75,
    "export_directory": "exports"
}


def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

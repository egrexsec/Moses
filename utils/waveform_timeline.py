from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt

from utils.timeline import load_timeline

WAVEFORM_DIR = Path("waveforms")
WAVEFORM_DIR.mkdir(exist_ok=True)


def generate_timeline_waveform(timeline_path):
    session = load_timeline(timeline_path)
    output_path = WAVEFORM_DIR / f"{session.session_id}_waveform.png"

    y, sr = librosa.load(session.audio_file, sr=None, mono=True)

    plt.figure(figsize=(14, 4))
    librosa.display.waveshow(y, sr=sr)

    for marker in session.markers:
        marker_time = float(marker["time_seconds"])
        plt.axvline(marker_time, linestyle="--")

    plt.title(session.title)
    plt.xlabel("Time in seconds")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return str(output_path)


def generate_region_waveform(audio_file, start_seconds, end_seconds):
    output_path = WAVEFORM_DIR / "region_waveform.png"

    y, sr = librosa.load(audio_file, sr=None, mono=True)

    start_sample = int(float(start_seconds) * sr)
    end_sample = int(float(end_seconds) * sr)

    region = y[start_sample:end_sample]

    plt.figure(figsize=(12, 3))
    librosa.display.waveshow(region, sr=sr)
    plt.title("Loop Region")
    plt.xlabel("Region Time")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return str(output_path)

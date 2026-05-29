from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path("spectrograms")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_spectrogram(audio_file):
    audio_path = Path(audio_file)
    output_path = OUTPUT_DIR / f"{audio_path.stem}_spectrogram.png"

    y, sr = librosa.load(audio_file)

    d = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)

    plt.figure(figsize=(12, 4))

    librosa.display.specshow(
        d,
        sr=sr,
        x_axis="time",
        y_axis="log"
    )

    plt.colorbar(format="%+2.0f dB")
    plt.title("Spectrogram")
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()

    return str(output_path)

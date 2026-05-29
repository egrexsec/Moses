from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt


OUTPUT_DIR = Path("spectrograms")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_waveform_image(audio_file):
    audio_path = Path(audio_file)
    output_path = OUTPUT_DIR / f"{audio_path.stem}_waveform.png"

    y, sr = librosa.load(audio_file)

    plt.figure(figsize=(10, 3))
    librosa.display.waveshow(y, sr=sr)
    plt.title("Waveform")
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()

    return str(output_path)

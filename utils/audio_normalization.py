from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


NORMALIZED_EXPORT_DIR = Path("exports/normalized")
NORMALIZED_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


TARGET_PEAK_DB = -1.0
TARGET_RMS_DB = -18.0



def db_to_linear(db_value):
    return 10 ** (db_value / 20.0)



def calculate_rms(audio):
    return np.sqrt(np.mean(np.square(audio)))



def normalize_peak(audio, target_peak_db=TARGET_PEAK_DB):
    peak = np.max(np.abs(audio))

    if peak == 0:
        return audio

    target_linear = db_to_linear(target_peak_db)

    gain = target_linear / peak

    return audio * gain



def normalize_rms(audio, target_rms_db=TARGET_RMS_DB):
    rms = calculate_rms(audio)

    if rms == 0:
        return audio

    target_linear = db_to_linear(target_rms_db)

    gain = target_linear / rms

    return audio * gain



def limiter(audio, ceiling_db=TARGET_PEAK_DB):
    ceiling = db_to_linear(ceiling_db)

    return np.clip(audio, -ceiling, ceiling)



def normalize_audio_file(audio_file, output_path=None):
    audio_path = Path(audio_file)

    if output_path is None:
        output_path = NORMALIZED_EXPORT_DIR / f"{audio_path.stem}_normalized.wav"

    y, sr = librosa.load(audio_file, sr=None, mono=False)

    y = normalize_rms(y)
    y = normalize_peak(y)
    y = limiter(y)

    if y.ndim > 1:
        y = y.T

    sf.write(output_path, y, sr)

    return str(output_path)



def batch_normalize_stems(stem_files):
    normalized = []

    for stem_file in stem_files:
        try:
            normalized_file = normalize_audio_file(stem_file)
            normalized.append(normalized_file)
        except Exception as exc:
            print(f"Normalization failed for {stem_file}: {exc}")

    return normalized



def analyze_audio_levels(audio_file):
    y, sr = librosa.load(audio_file, sr=None, mono=False)

    peak = np.max(np.abs(y))
    rms = calculate_rms(y)

    peak_db = 20 * np.log10(max(peak, 1e-10))
    rms_db = 20 * np.log10(max(rms, 1e-10))

    return {
        "audio_file": str(audio_file),
        "sample_rate": sr,
        "peak_db": round(float(peak_db), 2),
        "rms_db": round(float(rms_db), 2),
    }

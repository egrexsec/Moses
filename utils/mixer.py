import soundfile as sf
import numpy as np
from pathlib import Path


DEFAULT_GAINS = {
    "vocals": 1.0,
    "bass": 1.0,
    "drums": 1.0,
    "other": 1.0,
    "guitar": 1.0,
    "piano": 1.0,
}


DEFAULT_MUTES = {
    "vocals": False,
    "bass": False,
    "drums": False,
    "other": False,
    "guitar": False,
    "piano": False,
}


def detect_stem_type(stem_file):
    lower = Path(stem_file).name.lower()

    for stem_type in DEFAULT_GAINS.keys():
        if stem_type in lower:
            return stem_type

    return "other"


def mix_stems(
    stem_files,
    output_path,
    gains=None,
    mutes=None
):
    if gains is None:
        gains = DEFAULT_GAINS.copy()

    if mutes is None:
        mutes = DEFAULT_MUTES.copy()

    mixed_audio = None
    sample_rate = None

    for stem_file in stem_files:
        stem_type = detect_stem_type(stem_file)

        if mutes.get(stem_type, False):
            continue

        audio, sr = sf.read(stem_file)

        if sample_rate is None:
            sample_rate = sr

        gain = gains.get(stem_type, 1.0)

        audio = audio * gain

        if mixed_audio is None:
            mixed_audio = audio
        else:
            min_length = min(len(mixed_audio), len(audio))

            mixed_audio = (
                mixed_audio[:min_length] +
                audio[:min_length]
            )

    if mixed_audio is None:
        return None

    peak = np.max(np.abs(mixed_audio))

    if peak > 1.0:
        mixed_audio = mixed_audio / peak

    mixed_audio = np.clip(mixed_audio, -1.0, 1.0)

    sf.write(output_path, mixed_audio, sample_rate)

    return output_path

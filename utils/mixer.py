import soundfile as sf
import numpy as np
from pathlib import Path


def mix_stems(stem_files, output_path, gains=None):
    if gains is None:
        gains = {}

    mixed_audio = None
    sample_rate = None

    for stem_file in stem_files:
        audio, sr = sf.read(stem_file)

        if sample_rate is None:
            sample_rate = sr

        gain = gains.get(Path(stem_file).stem.lower(), 1.0)

        audio = audio * gain

        if mixed_audio is None:
            mixed_audio = audio
        else:
            min_length = min(len(mixed_audio), len(audio))
            mixed_audio = mixed_audio[:min_length] + audio[:min_length]

    if mixed_audio is None:
        return None

    mixed_audio = np.clip(mixed_audio, -1.0, 1.0)

    sf.write(output_path, mixed_audio, sample_rate)

    return output_path

from pathlib import Path

import librosa



def detect_bpm(audio_file):
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    tempo, _ = librosa.beat.beat_track(
        y=y,
        sr=sr,
    )

    return round(float(tempo), 2)



def detect_key(audio_file):
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    keys = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]

    key_index = chroma_mean.argmax()

    return keys[key_index]



def analyze_song_metadata(audio_file):
    audio_path = Path(audio_file)

    bpm = detect_bpm(audio_file)
    key = detect_key(audio_file)

    return {
        "song_name": audio_path.stem,
        "audio_file": str(audio_path),
        "bpm": bpm,
        "musical_key": key,
    }

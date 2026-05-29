import librosa


def detect_bpm_and_key(audio_file):
    try:
        y, sr = librosa.load(audio_file)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()

        keys = [
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B"
        ]

        return {
            "bpm": round(float(tempo), 2),
            "key": keys[key_index]
        }

    except Exception:
        return None

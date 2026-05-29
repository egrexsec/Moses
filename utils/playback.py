import librosa
import soundfile as sf


def create_slowed_version(audio_file, output_file, rate=0.75):
    y, sr = librosa.load(audio_file, sr=None)

    slowed = librosa.effects.time_stretch(y, rate=rate)

    sf.write(output_file, slowed, sr)

    return output_file

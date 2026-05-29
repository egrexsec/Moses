import shutil
import subprocess


def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


def get_audio_info(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        duration = float(result.stdout.strip())
        return {
            "duration_seconds": duration,
            "duration_minutes": round(duration / 60, 2),
        }
    except:
        return None

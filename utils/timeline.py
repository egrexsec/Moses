import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

import librosa
import soundfile as sf


TIMELINE_DIR = Path("timelines")
TIMELINE_DIR.mkdir(exist_ok=True)


@dataclass
class TimelineMarker:
    name: str
    time_seconds: float
    marker_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notes: str = ""


@dataclass
class TimelineLoop:
    name: str
    start_seconds: float
    end_seconds: float
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notes: str = ""


@dataclass
class TimelineSession:
    audio_file: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Timeline"
    duration_seconds: float = 0.0
    sample_rate: int = 0
    markers: list = field(default_factory=list)
    loops: list = field(default_factory=list)


def analyze_audio_for_timeline(audio_file, title=None):
    y, sr = librosa.load(audio_file, sr=None, mono=False)

    if y.ndim > 1:
        sample_count = y.shape[-1]
    else:
        sample_count = len(y)

    duration = sample_count / sr

    return TimelineSession(
        audio_file=audio_file,
        title=title or Path(audio_file).stem,
        duration_seconds=round(duration, 3),
        sample_rate=sr,
    )


def save_timeline(session):
    output_path = TIMELINE_DIR / f"{session.session_id}.json"

    with open(output_path, "w") as f:
        json.dump(asdict(session), f, indent=4)

    return str(output_path)


def load_timeline(timeline_path):
    with open(timeline_path, "r") as f:
        data = json.load(f)

    session = TimelineSession(
        audio_file=data["audio_file"],
        session_id=data["session_id"],
        title=data.get("title", "Untitled Timeline"),
        duration_seconds=data.get("duration_seconds", 0.0),
        sample_rate=data.get("sample_rate", 0),
    )

    session.markers = data.get("markers", [])
    session.loops = data.get("loops", [])

    return session


def add_marker(timeline_path, name, time_seconds, notes=""):
    session = load_timeline(timeline_path)
    marker = TimelineMarker(
        name=name,
        time_seconds=float(time_seconds),
        notes=notes or ""
    )

    session.markers.append(asdict(marker))
    save_timeline(session)

    return marker


def add_loop(timeline_path, name, start_seconds, end_seconds, notes=""):
    session = load_timeline(timeline_path)

    start = float(start_seconds)
    end = float(end_seconds)

    if end <= start:
        raise ValueError("Loop end time must be greater than start time.")

    loop = TimelineLoop(
        name=name,
        start_seconds=start,
        end_seconds=end,
        notes=notes or ""
    )

    session.loops.append(asdict(loop))
    save_timeline(session)

    return loop


def export_loop_region(audio_file, start_seconds, end_seconds, output_path):
    y, sr = librosa.load(audio_file, sr=None, mono=False)

    start_sample = int(float(start_seconds) * sr)
    end_sample = int(float(end_seconds) * sr)

    if y.ndim > 1:
        region = y[:, start_sample:end_sample]
        region = region.T
    else:
        region = y[start_sample:end_sample]

    sf.write(output_path, region, sr)

    return output_path


def timeline_summary(timeline_path):
    session = load_timeline(timeline_path)

    lines = [
        f"Timeline: {session.title}",
        f"Audio: {session.audio_file}",
        f"Duration: {session.duration_seconds} seconds",
        f"Sample Rate: {session.sample_rate}",
        "",
        "Markers:",
    ]

    if not session.markers:
        lines.append("- None")
    else:
        for marker in session.markers:
            lines.append(
                f"- {marker['name']} @ {marker['time_seconds']}s — {marker.get('notes', '')}"
            )

    lines.extend(["", "Loops:"])

    if not session.loops:
        lines.append("- None")
    else:
        for loop in session.loops:
            lines.append(
                f"- {loop['name']}: {loop['start_seconds']}s to {loop['end_seconds']}s — {loop.get('notes', '')}"
            )

    return "\n".join(lines)

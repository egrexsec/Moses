import time
from dataclasses import dataclass, asdict


@dataclass
class PlaybackState:
    audio_file: str = ""
    is_playing: bool = False
    position_seconds: float = 0.0
    loop_enabled: bool = False
    loop_start: float = 0.0
    loop_end: float = 0.0
    playback_rate: float = 1.0
    updated_at: float = 0.0


class PlaybackTransport:
    def __init__(self):
        self.state = PlaybackState(updated_at=time.time())

    def load(self, audio_file):
        self.state = PlaybackState(
            audio_file=audio_file,
            is_playing=False,
            position_seconds=0.0,
            updated_at=time.time()
        )
        return self.status_text()

    def play(self):
        self.state.is_playing = True
        self.state.updated_at = time.time()
        return self.status_text()

    def pause(self):
        self.state.is_playing = False
        self.state.updated_at = time.time()
        return self.status_text()

    def stop(self):
        self.state.is_playing = False
        self.state.position_seconds = 0.0
        self.state.updated_at = time.time()
        return self.status_text()

    def seek(self, position_seconds):
        self.state.position_seconds = max(float(position_seconds or 0), 0.0)
        self.state.updated_at = time.time()
        return self.status_text()

    def set_loop(self, start_seconds, end_seconds):
        start = max(float(start_seconds or 0), 0.0)
        end = max(float(end_seconds or 0), start)

        self.state.loop_enabled = end > start
        self.state.loop_start = start
        self.state.loop_end = end
        self.state.updated_at = time.time()

        return self.status_text()

    def clear_loop(self):
        self.state.loop_enabled = False
        self.state.loop_start = 0.0
        self.state.loop_end = 0.0
        self.state.updated_at = time.time()
        return self.status_text()

    def set_rate(self, playback_rate):
        self.state.playback_rate = max(float(playback_rate or 1.0), 0.25)
        self.state.updated_at = time.time()
        return self.status_text()

    def as_dict(self):
        return asdict(self.state)

    def status_text(self):
        state = "Playing" if self.state.is_playing else "Paused"
        loop = "Off"

        if self.state.loop_enabled:
            loop = f"{self.state.loop_start}s → {self.state.loop_end}s"

        return "\n".join([
            f"Audio: {self.state.audio_file or 'None'}",
            f"State: {state}",
            f"Position: {self.state.position_seconds}s",
            f"Playback Rate: {self.state.playback_rate}x",
            f"Loop: {loop}",
        ])


transport = PlaybackTransport()

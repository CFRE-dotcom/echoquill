"""Optional audio history: keep the recording of each dictation on-device,
with a size budget and ZIP export. Off by default (privacy-first)."""

import time
import wave
from pathlib import Path

import numpy as np

from .config import app_data_dir
from .audio import SAMPLE_RATE

AUDIO_DIR = app_data_dir() / "audio_history"


def _dir() -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_DIR


def save(audio: np.ndarray, cfg: dict):
    """Write one dictation's audio as a WAV, then enforce the size budget."""
    if not cfg.get("keep_audio", False) or audio is None or len(audio) < 1600:
        return
    try:
        d = _dir()
        name = time.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
        pcm = np.clip(audio, -1.0, 1.0)
        pcm = (pcm * 32767).astype("<i2")
        with wave.open(str(d / name), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm.tobytes())
        _enforce_budget(cfg.get("audio_max_mb", 500))
    except Exception:
        pass


def _enforce_budget(max_mb: int):
    d = _dir()
    files = sorted(d.glob("*.wav"), key=lambda f: f.stat().st_mtime)
    total = sum(f.stat().st_size for f in files)
    limit = max_mb * 1024 * 1024
    i = 0
    while total > limit and i < len(files):
        try:
            total -= files[i].stat().st_size
            files[i].unlink()
        except Exception:
            pass
        i += 1


def usage_mb() -> float:
    try:
        return round(sum(f.stat().st_size for f in _dir().glob("*.wav")) / 1048576, 1)
    except Exception:
        return 0.0


def count() -> int:
    try:
        return len(list(_dir().glob("*.wav")))
    except Exception:
        return 0


def export_zip(dest_path: str) -> bool:
    import zipfile
    try:
        with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as z:
            for f in _dir().glob("*.wav"):
                z.write(f, f.name)
        return True
    except Exception:
        return False


def clear():
    for f in _dir().glob("*.wav"):
        try:
            f.unlink()
        except Exception:
            pass

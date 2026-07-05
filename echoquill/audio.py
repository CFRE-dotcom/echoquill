"""Microphone recording for EchoQuill.

Community-feedback improvements built in:
- Start cue plays only AFTER the stream is live, so the first word is never missed.
- Tail recording keeps capturing briefly after stop, so the last word isn't cut off.
- Microphone lock: always use the user's chosen mic, even if Windows changes default.
- Media ducking: lower other apps' volume while dictating instead of pausing them.
"""

import threading
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000  # what Whisper expects


def list_input_devices():
    """Return [(index, name)] of available input devices."""
    devices = []
    try:
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                devices.append((i, d["name"]))
    except Exception:
        pass
    return devices


def find_device(preferred_name: str):
    """Resolve the preferred mic by (partial) name; None = system default."""
    if not preferred_name:
        return None
    for idx, name in list_input_devices():
        if preferred_name.lower() in name.lower():
            return idx
    return None  # fall back to default if the preferred mic is unplugged


class MediaDucker:
    """Lower the volume of other apps while dictating (Windows, via pycaw).

    Fails silently if pycaw isn't available - ducking is a nicety, not a need.
    """

    DUCK_LEVEL = 0.25

    def __init__(self):
        self._saved = []

    def duck(self):
        try:
            from pycaw.pycaw import AudioUtilities
            for session in AudioUtilities.GetAllSessions():
                try:
                    vol = session.SimpleAudioVolume
                    current = vol.GetMasterVolume()
                    if current > self.DUCK_LEVEL:
                        self._saved.append((vol, current))
                        vol.SetMasterVolume(self.DUCK_LEVEL, None)
                except Exception:
                    continue
        except Exception:
            pass

    def restore(self):
        for vol, level in self._saved:
            try:
                vol.SetMasterVolume(level, None)
            except Exception:
                continue
        self._saved = []


def play_cue(start: bool = True):
    """Short audible cue. Uses winsound (built into Windows Python)."""
    try:
        import winsound
        winsound.Beep(880 if start else 440, 90)
    except Exception:
        pass


class Recorder:
    """Records 16 kHz mono audio between start() and stop()."""

    def __init__(self, preferred_mic: str = "", tail_ms: int = 400,
                 start_cue: bool = True, end_cue: bool = True,
                 duck_media: bool = True):
        self.preferred_mic = preferred_mic
        self.tail_ms = max(0, int(tail_ms))
        self.start_cue = start_cue
        self.end_cue = end_cue
        self.duck_media = duck_media

        self._chunks = []
        self._stream = None
        self._lock = threading.Lock()
        self._recording = False
        self._ducker = MediaDucker()
        self.level = 0.0  # live mic level 0..1 for waveform animation

    @property
    def recording(self) -> bool:
        return self._recording

    def _callback(self, indata, frames, time_info, status):
        with self._lock:
            if self._recording:
                self._chunks.append(indata.copy())
        try:
            self.level = float(min(1.0, (abs(indata).mean() * 12)))
        except Exception:
            pass

    def start(self):
        if self._recording:
            return
        self._chunks = []
        device = find_device(self.preferred_mic)
        if self.duck_media:
            self._ducker.duck()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=device,
            callback=self._callback,
        )
        self._stream.start()
        self._recording = True
        # Cue AFTER the stream is live -> user can start talking immediately
        if self.start_cue:
            play_cue(start=True)

    def snapshot(self) -> np.ndarray:
        """Copy of everything recorded so far (for live preview)."""
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._chunks, axis=0).flatten().astype(np.float32)

    def stop(self) -> np.ndarray:
        """Stop recording (after the tail window) and return mono float32 audio."""
        if not self._recording:
            return np.zeros(0, dtype=np.float32)
        # Tail recording: catch the last word/syllable
        if self.tail_ms:
            time.sleep(self.tail_ms / 1000.0)
        with self._lock:
            self._recording = False
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        self._stream = None
        if self.duck_media:
            self._ducker.restore()
        if self.end_cue:
            play_cue(start=False)
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0).flatten()
            self._chunks = []
        return audio.astype(np.float32)

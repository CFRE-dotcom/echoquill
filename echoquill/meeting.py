"""Meeting mode: record what you HEAR (system audio) plus, optionally, your
mic, then transcribe it locally with the same Whisper engine.

Great for calls, webinars, and ANY video that plays on your PC (including
Skool) - no URL, no link-grabbing, no DevTools. Uses WASAPI loopback via the
`soundcard` package; degrades gracefully if that isn't available.
"""

import threading

import numpy as np

SR = 16000  # Whisper wants 16 kHz mono


def available() -> bool:
    try:
        import soundcard  # noqa: F401
        return True
    except Exception:
        return False


class MeetingRecorder:
    def __init__(self, include_mic: bool = False):
        self.include_mic = include_mic
        self._frames = []
        self._running = False
        self._thread = None
        self._error = None
        self._started = None

    # ---------- control ----------
    def start(self):
        self._frames = []
        self._error = None
        self._running = True
        import time
        self._started = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> "np.ndarray | None":
        self._running = False
        if self._thread:
            self._thread.join(timeout=8)
        if self._error:
            raise RuntimeError(self._error)
        if not self._frames:
            return None
        return np.concatenate(self._frames)

    def elapsed(self) -> float:
        import time
        return (time.time() - self._started) if self._started else 0.0

    # ---------- capture loop ----------
    def _loop(self):
        try:
            import soundcard as sc
            spk = sc.default_speaker()
            loopback = sc.get_microphone(id=str(spk.name), include_loopback=True)
            block = 4000
            mic = sc.default_microphone() if self.include_mic else None
            with loopback.recorder(samplerate=SR, channels=1) as lrec:
                mrec = None
                mctx = None
                if mic is not None:
                    mctx = mic.recorder(samplerate=SR, channels=1)
                    mrec = mctx.__enter__()
                try:
                    while self._running:
                        sysd = lrec.record(numframes=block)
                        sysm = sysd.mean(axis=1) if sysd.ndim > 1 else sysd
                        if mrec is not None:
                            micd = mrec.record(numframes=block)
                            micm = micd.mean(axis=1) if micd.ndim > 1 else micd
                            n = min(len(sysm), len(micm))
                            mixed = np.clip(sysm[:n] + micm[:n], -1.0, 1.0)
                        else:
                            mixed = sysm
                        self._frames.append(np.asarray(mixed, dtype=np.float32))
                finally:
                    if mctx is not None:
                        mctx.__exit__(None, None, None)
        except Exception as e:  # surfaced by stop()
            self._error = str(e)
            self._running = False


def save_wav(audio: "np.ndarray", path: str):
    """Write a mono float32 array to a 16-bit PCM WAV."""
    import wave
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

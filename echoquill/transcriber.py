"""Local speech-to-text using faster-whisper (free, offline, open source).

Model sizes are the "speed settings": tiny/base are near-instant, small/medium
are more accurate, large-v3 is the most accurate with 99-language support.
Models download automatically the first time they're used, then run offline.
"""

import threading

import numpy as np


class Transcriber:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self._lock = threading.Lock()

    def load(self):
        """Load (or reload) the model. Called lazily on first transcription."""
        from faster_whisper import WhisperModel
        with self._lock:
            if self._model is None:
                # int8 keeps memory low and speed high on ordinary desktops;
                # faster-whisper picks GPU automatically if CUDA is available.
                self._model = WhisperModel(
                    self.model_size, device="auto", compute_type="int8"
                )
        return self._model

    def set_model(self, model_size: str):
        if model_size != self.model_size:
            with self._lock:
                self.model_size = model_size
                self._model = None  # reload lazily with the new size

    def transcribe(self, audio: np.ndarray, language: str = "auto") -> str:
        if audio is None or len(audio) < 1600:  # <0.1s of audio
            return ""
        model = self.load()
        lang = None if language in ("", "auto") else language
        with self._lock:
            segments, _info = model.transcribe(
            audio,
            language=lang,
            vad_filter=True,           # skip silence for speed
            beam_size=1,               # greedy = fastest; accuracy comes from model size
            condition_on_previous_text=False,
            )
            return " ".join(seg.text.strip() for seg in segments).strip()

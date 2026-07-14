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
        import ctypes
        _co = False
        try:
            # WASAPI capture threads want COM in the MULTITHREADED apartment,
            # otherwise record() can return no samples (or 0x800401F0).
            ctypes.windll.ole32.CoInitializeEx(None, 0)  # 0 = COINIT_MULTITHREADED
            _co = True
        except Exception:
            try:
                ctypes.windll.ole32.CoInitialize(None)
                _co = True
            except Exception:
                pass
        try:
            import soundcard as sc

            # find a loopback capture of the current default output device
            spk = sc.default_speaker()
            loop_src = None
            try:
                loop_src = sc.get_microphone(id=str(spk.name), include_loopback=True)
            except Exception:
                loop_src = None
            if loop_src is None:
                loops = [m for m in sc.all_microphones(include_loopback=True)
                         if getattr(m, "isloopback", False)]
                # prefer one whose name matches the default speaker
                match = [m for m in loops if spk.name.lower() in m.name.lower()]
                loop_src = (match or loops or [None])[0]
            if loop_src is None:
                self._error = "No system-audio (loopback) device found."
                self._running = False
                return

            block = 2400
            mic = sc.default_microphone() if self.include_mic else None
            with loop_src.recorder(samplerate=SR, channels=1) as lrec:
                mrec = None
                mctx = None
                if mic is not None:
                    try:
                        mctx = mic.recorder(samplerate=SR, channels=1)
                        mrec = mctx.__enter__()
                    except Exception:
                        mrec = None
                        mctx = None
                try:
                    while self._running:
                        sysd = lrec.record(numframes=block)
                        sysm = sysd.mean(axis=1) if sysd.ndim > 1 else sysd
                        if mrec is not None:
                            try:
                                micd = mrec.record(numframes=block)
                                micm = micd.mean(axis=1) if micd.ndim > 1 else micd
                                n = min(len(sysm), len(micm))
                                mixed = np.clip(sysm[:n] + micm[:n], -1.0, 1.0)
                            except Exception:
                                mixed = sysm
                        else:
                            mixed = sysm
                        if len(mixed):
                            self._frames.append(np.asarray(mixed, dtype=np.float32))
                finally:
                    if mctx is not None:
                        try:
                            mctx.__exit__(None, None, None)
                        except Exception:
                            pass
        except Exception as e:  # surfaced by stop()
            self._error = str(e)
            self._running = False
        finally:
            if _co:
                try:
                    ctypes.windll.ole32.CoUninitialize()
                except Exception:
                    pass

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


class ScreenRecorder:
    """Records the whole desktop (ffmpeg gdigrab) AND system audio (loopback,
    + optional mic), then muxes them into one MP4. Windows-only.

    Same control surface as MeetingRecorder (start / stop -> audio / elapsed),
    so the UI can use either interchangeably. stop() returns the audio array
    for transcription; the muxed .mp4 is written to `dest`."""

    def __init__(self, dest_mp4: str, include_mic: bool = False, fps: int = 15):
        self.dest = dest_mp4
        self.fps = fps
        self.error = None
        self._audio = MeetingRecorder(include_mic=include_mic)
        self._proc = None
        self._screen_tmp = None

    @property
    def _running(self):
        return self._audio._running

    def elapsed(self):
        return self._audio.elapsed()

    def _ffmpeg(self):
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()

    def start(self):
        import os
        import subprocess
        import tempfile
        self._screen_tmp = os.path.join(tempfile.gettempdir(), "eq_screen.mp4")
        ff = self._ffmpeg()
        args = [ff, "-y", "-f", "gdigrab", "-framerate", str(self.fps),
                "-i", "desktop", "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", self._screen_tmp]
        try:
            self._proc = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, creationflags=0x08000000)
        except Exception as e:
            self.error = f"screen capture: {e}"
            self._proc = None
        self._audio.start()   # audio in parallel

    def stop(self):
        import os
        import subprocess
        # finalize the screen recording (tell ffmpeg to quit gracefully)
        try:
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.communicate(b"q", timeout=10)
                except Exception:
                    self._proc.terminate()
        except Exception:
            pass
        audio = self._audio.stop()
        # write the audio to a wav and mux with the screen video
        try:
            import tempfile
            ff = self._ffmpeg()
            has_video = self._screen_tmp and os.path.exists(self._screen_tmp)
            if audio is not None and has_video:
                wav = os.path.join(tempfile.gettempdir(), "eq_audio.wav")
                save_wav(audio, wav)
                subprocess.run(
                    [ff, "-y", "-i", self._screen_tmp, "-i", wav,
                     "-c:v", "copy", "-c:a", "aac", "-shortest", self.dest],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=0x08000000, timeout=300)
            elif has_video:
                os.replace(self._screen_tmp, self.dest)
        except Exception as e:
            self.error = f"mux: {e}"
        finally:
            # tidy temp files so they don't accumulate
            for tmp in (self._screen_tmp,
                        os.path.join(__import__("tempfile").gettempdir(), "eq_audio.wav")):
                try:
                    if tmp and os.path.exists(tmp) and tmp != self.dest:
                        os.remove(tmp)
                except Exception:
                    pass
        return audio

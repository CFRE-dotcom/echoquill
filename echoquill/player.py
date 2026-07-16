"""A small audio player with pause + a seekable timeline, built on Windows'
built-in MCI (winmm) via ctypes - no external libraries, no ffmpeg.

AudioPlayer is a ttk.Frame you drop into a window: [Play/Pause] [Stop]
0:00 [=====timeline=====] 3:12. It plays a WAV file, and once generated the
audio replays/scrubs for free (no new API credits).
"""

import ctypes
import tkinter as tk
from tkinter import ttk

from . import theme

_mci = ctypes.windll.winmm.mciSendStringW if hasattr(ctypes, "windll") else None


def _cmd(s):
    if _mci is None:
        return 1, ""
    buf = ctypes.create_unicode_buffer(256)
    err = _mci(s, buf, 256, None)
    return err, buf.value


def _fmt(ms):
    s = int(max(0, ms) // 1000)
    return f"{s // 60}:{s % 60:02d}"


class MCIPlayer:
    def __init__(self):
        self.alias = f"eq{id(self)}"
        self.loaded = False
        self._path = None

    def load(self, path):
        self.close()                         # releases the previous file lock
        if self._path and self._path != path:
            try:
                import os
                os.remove(self._path)        # clean up the old temp wav
            except Exception:
                pass
        _cmd(f'open "{path}" type waveaudio alias {self.alias}')
        _cmd(f'set {self.alias} time format milliseconds')
        self._path = path
        self.loaded = True

    def play(self, from_ms=None):
        if not self.loaded:
            return
        if from_ms is not None:
            _cmd(f'play {self.alias} from {int(from_ms)}')
        else:
            _cmd(f'play {self.alias}')

    def pause(self):
        _cmd(f'pause {self.alias}')

    def resume(self):
        _cmd(f'resume {self.alias}')

    def stop(self):
        _cmd(f'stop {self.alias}')

    def seek(self, ms):
        _cmd(f'seek {self.alias} to {int(ms)}')

    def length(self):
        _e, v = _cmd(f'status {self.alias} length')
        try:
            return int(v)
        except Exception:
            return 0

    def position(self):
        _e, v = _cmd(f'status {self.alias} position')
        try:
            return int(v)
        except Exception:
            return 0

    def mode(self):
        _e, v = _cmd(f'status {self.alias} mode')
        return (v or "").strip()

    def close(self):
        if self.loaded:
            _cmd(f'close {self.alias}')
            self.loaded = False


class AudioPlayer(ttk.Frame):
    """Transport bar. Call load_and_play(wav_path) to start."""

    def __init__(self, parent, win, on_generate=None):
        super().__init__(parent)
        self.win = win
        self.on_generate = on_generate      # called to (re)build audio on Play
        self.mci = MCIPlayer()
        self._len = 1
        self._drag = False
        self._job = None
        self._stale = True                  # text changed -> regenerate next Play

        self.play_btn = ttk.Button(self, text="▶ Play",
                                   style="Accent.TButton", command=self._toggle)
        self.play_btn.pack(side="left")
        self.stop_btn = ttk.Button(self, text="■", width=3, command=self.stop)
        self.stop_btn.pack(side="left", padx=(6, 8))
        self.cur = ttk.Label(self, text="0:00", style="Dim.TLabel")
        self.cur.pack(side="left")
        self.scale = ttk.Scale(self, from_=0, to=1000, orient="horizontal",
                               command=self._on_scale)
        self.scale.pack(side="left", fill="x", expand=True, padx=8)
        self.tot = ttk.Label(self, text="0:00", style="Dim.TLabel")
        self.tot.pack(side="left")
        self.scale.bind("<Button-1>", lambda e: setattr(self, "_drag", True))
        self.scale.bind("<ButtonRelease-1>", self._seek_release)
        self._set_enabled(False)

    # ---- public ----

    def load_and_play(self, wav_path):
        self.mci.load(wav_path)
        self._len = max(1, self.mci.length())
        self.tot.configure(text=_fmt(self._len))
        self._stale = False
        self._set_enabled(True)
        self.mci.play()
        self.play_btn.configure(text="⏸ Pause")
        self._tick()

    def invalidate(self):
        """Mark the audio out of date (text edited) so Play regenerates."""
        self._stale = True

    def shutdown(self):
        if self._job:
            try:
                self.win.after_cancel(self._job)
            except Exception:
                pass
        self.mci.close()

    # ---- internals ----

    def _set_enabled(self, on):
        st = "normal" if on else "disabled"
        for w in (self.stop_btn, self.scale):   # Play stays enabled to generate
            try:
                w.configure(state=st)
            except Exception:
                pass

    def _toggle(self):
        if self.on_generate and (self._stale or not self.mci.loaded):
            self.on_generate()                  # (re)generate, then load_and_play
            return
        m = self.mci.mode()
        if m == "playing":
            self.mci.pause()
            self.play_btn.configure(text="▶ Play")
        elif m == "paused":
            self.mci.resume()
            self.play_btn.configure(text="⏸ Pause")
            self._tick()
        else:                                   # stopped/ended -> free relisten
            self.mci.play(from_ms=0)
            self.play_btn.configure(text="⏸ Pause")
            self._tick()

    def stop(self):
        self.mci.stop()
        self.mci.seek(0)
        self.play_btn.configure(text="▶ Play")
        self.scale.set(0)
        self.cur.configure(text="0:00")

    def _on_scale(self, val):
        if self._drag:
            self.cur.configure(text=_fmt(self._len * float(val) / 1000.0))

    def _seek_release(self, _e):
        frac = float(self.scale.get()) / 1000.0
        ms = self._len * frac
        self.mci.seek(ms)
        if self.mci.mode() != "playing":
            self.mci.play(from_ms=ms)
            self.play_btn.configure(text="⏸ Pause")
        self._drag = False
        self._tick()

    def _tick(self):
        if self._drag:
            self._job = self.win.after(200, self._tick)
            return
        pos = self.mci.position()
        try:
            self.scale.set(1000 * pos / self._len)
        except Exception:
            pass
        self.cur.configure(text=_fmt(pos))
        m = self.mci.mode()
        if m == "playing":
            self._job = self.win.after(200, self._tick)
        else:
            self.play_btn.configure(text="▶ Play")

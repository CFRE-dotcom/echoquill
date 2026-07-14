"""Rounded, always-on-top dictation pill - bottom-center, Wispr-Flow style.

Idle:      small rounded pill with a mic glyph. Click to dictate.
Recording: pill widens - your words appear live above animated waveform bars.
Right-click: menu (Clips tray, Transcribe video, Settings, Stats, Quit).

True rounded corners via a Windows transparent-color window; everything is
drawn on one canvas. The window never steals keyboard focus.
"""

import tkinter as tk
from collections import deque

TRANSPARENT = "#010203"          # this exact color becomes see-through
BG = "#1c1c1e"
FG = "#f2f2f7"
DIM = "#98989d"
ACCENT = "#0a84ff"
ACCENT_DARK = "#0868c8"
ACCENT_BUSY = ACCENT
BAR = "#f2f2f7"

N_BARS = 30


def _rounded(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


_TRANS_RGB = (1, 2, 3)          # matches TRANSPARENT hex
_pill_cache = {}


def _pill_photo(w, h, fill, outline):
    """Smooth rounded pill with crisp edges (no gradient halo).

    Drawn 4x oversized on a transparent layer, downscaled, then the edge
    alpha is thresholded so every pixel is either pill or fully invisible -
    clean curves without the blurry fade the previous version had.
    """
    key = (w, h, fill, outline)
    if key in _pill_cache:
        return _pill_cache[key]
    from PIL import Image, ImageDraw, ImageTk
    S = 4
    layer = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([2 * S, 2 * S, (w - 2) * S, (h - 2) * S],
                        radius=(h // 2 - 2) * S, fill=fill,
                        outline=outline, width=S)
    layer = layer.resize((w, h), Image.LANCZOS)
    base = Image.new("RGB", (w, h), _TRANS_RGB)
    mask = layer.getchannel("A").point(lambda a: 255 if a >= 140 else 0)
    base.paste(layer.convert("RGB"), (0, 0), mask)
    photo = ImageTk.PhotoImage(base)
    _pill_cache[key] = photo
    return photo


class Overlay:
    IDLE_W, IDLE_H = 68, 38
    LIVE_W, LIVE_H = 480, 74

    def __init__(self, root: tk.Tk, on_toggle=None, on_settings=None,
                 on_stats=None, on_quit=None, on_history=None,
                 on_clips=None, on_media=None, on_command=None,
                 on_help=None, on_meeting=None, level_provider=None):
        self.root = root
        self.on_toggle = on_toggle
        self.on_settings = on_settings
        self.on_stats = on_stats
        self.on_quit = on_quit
        self.on_history = on_history
        self.on_clips = on_clips
        self.on_media = on_media
        self.on_command = on_command
        self.on_help = on_help
        self.on_meeting = on_meeting
        self.level_provider = level_provider or (lambda: 0.0)
        self.win = None
        self.canvas = None
        self.idle_text = "🎙"
        self._result_job = None
        self._anim_job = None
        self._mode = "idle"
        self._live_text = ""
        self._levels = deque([0.0] * N_BARS, maxlen=N_BARS)
        self._smooth = 0.0

    # ---------- window ----------

    def _ensure(self):
        if self.win is not None:
            return
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=TRANSPARENT)
        try:
            self.win.attributes("-transparentcolor", TRANSPARENT)
        except Exception:
            self.win.configure(bg=BG)   # fallback: square but functional
        self.canvas = tk.Canvas(self.win, bg=TRANSPARENT,
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._clicked)
        self.canvas.bind("<Button-3>", self._menu)
        self._no_focus_steal()

    def _no_focus_steal(self):
        try:
            import ctypes
            self.win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            GWL_EXSTYLE = -20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | 0x08000000 | 0x00000080)
        except Exception:
            pass

    def _clicked(self, _e=None):
        if self.on_toggle:
            self.on_toggle()
        return "break"

    def _menu(self, e):
        m = tk.Menu(self.win, tearoff=0, bg=BG, fg=FG,
                    activebackground="#3a3a3c", activeforeground=FG, bd=0)
        m.add_command(label="Start / stop dictation", command=self._clicked)
        if self.on_command:
            m.add_command(label="Voice command — tell the PC what to do",
                          command=self.on_command)
        if self.on_clips:
            m.add_command(label="Clips tray (recent 10)", command=self.on_clips)
        if self.on_media:
            m.add_command(label="Transcribe video / URL…", command=self.on_media)
        if self.on_meeting:
            m.add_command(label="Meeting / Record…", command=self.on_meeting)
        if self.on_history:
            m.add_command(label="All recent transcriptions…", command=self.on_history)
        if self.on_settings:
            m.add_command(label="Settings…", command=self.on_settings)
        if self.on_stats:
            m.add_command(label="Today's stats", command=self.on_stats)
        if self.on_help:
            m.add_command(label="Help & how-to…", command=self.on_help)
        m.add_separator()
        if self.on_quit:
            m.add_command(label="Quit EchoQuill", command=self.on_quit)
        m.tk_popup(e.x_root, e.y_root)
        return "break"

    def _place(self, w, h):
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.canvas.configure(width=w, height=h)
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{sh - h - 58}")

    def _cancel_jobs(self, result=True, anim=True):
        for attr, flag in (("_result_job", result), ("_anim_job", anim)):
            job = getattr(self, attr)
            if job and flag:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
                setattr(self, attr, None)

    # ---------- drawing ----------

    def _draw_pill(self, w, h, fill=BG, outline="#3a3a3c"):
        self.canvas.delete("all")
        try:
            self._pill_img = _pill_photo(w, h, fill, outline)
            self.canvas.create_image(0, 0, anchor="nw", image=self._pill_img)
        except Exception:
            _rounded(self.canvas, 2, 2, w - 2, h - 2, h // 2 - 2,
                     fill=fill, outline=outline)

    def _draw_idle(self):
        w, h = self.IDLE_W, self.IDLE_H
        self._place(w, h)
        self._draw_pill(w, h, fill=ACCENT, outline=ACCENT_DARK)
        self.canvas.create_text(w / 2, h / 2, text=self.idle_text,
                                fill="#ffffff", font=("Segoe UI Emoji", 13))

    def _draw_live(self):
        w, h = self.LIVE_W, self.LIVE_H
        self._place(w, h)
        self._draw_pill(w, h)
        text = self._live_text or "Listening…"
        shown = text[-64:] if len(text) > 64 else text
        self.canvas.create_text(w / 2, 22, text=shown,
                                fill=FG if self._live_text else DIM,
                                font=("Segoe UI", 11), width=w - 50)

    def _draw_bars(self):
        """Flowing waveform: each bar is a moment of your voice, scrolling
        left as you speak - smooth rounded bars, newest on the right."""
        self.canvas.delete("bars")
        w, h = self.LIVE_W, self.LIVE_H
        level = 0.0
        try:
            level = max(0.0, min(1.0, float(self.level_provider())))
        except Exception:
            pass
        # gentle smoothing so bars breathe instead of twitching
        self._smooth = 0.55 * self._smooth + 0.45 * level
        self._levels.append(self._smooth)
        span = w - 160
        mid = h - 22
        step = span / N_BARS
        x0 = (w - span) / 2
        for i, lv in enumerate(self._levels):
            x = x0 + (i + 0.5) * step
            bh = 3 + lv * 24
            self.canvas.create_line(x, mid - bh / 2, x, mid + bh / 2,
                                    width=3, capstyle="round",
                                    fill=BAR, tags="bars")

    def _animate(self):
        if self._mode != "recording":
            return
        self._draw_bars()
        self._anim_job = self.root.after(66, self._animate)

    def _text_pill(self, text, color, width=None):
        est = max(self.IDLE_W, min(560, 40 + 8 * len(text)))
        w = width or est
        h = self.IDLE_H + 8
        self._place(w, h)
        self._draw_pill(w, h)
        self.canvas.create_text(w / 2, h / 2, text=text, fill=color,
                                font=("Segoe UI", 11), width=w - 30)

    # ---------- states ----------

    def show_idle(self):
        self._ensure()
        self._cancel_jobs()
        self._mode = "idle"
        self._draw_idle()

    def show_recording(self):
        self._ensure()
        self._cancel_jobs()
        self._mode = "recording"
        self._live_text = ""
        self._levels.clear()
        self._levels.extend([0.0] * N_BARS)
        self._smooth = 0.0
        self._draw_live()
        self._animate()

    def show_live(self, text: str):
        self._ensure()
        self._live_text = text or ""
        if self._mode != "recording":
            self._cancel_jobs()
            self._mode = "recording"
            self._animate()
        self._draw_live()

    def show_busy(self):
        self._ensure()
        self._cancel_jobs()
        self._mode = "busy"
        self._text_pill("✎  Finishing…", ACCENT_BUSY, width=170)

    def show_result(self, text: str, ms: int = 2400):
        self._ensure()
        self._cancel_jobs()
        self._mode = "result"
        shown = text if len(text) <= 90 else text[:87] + "…"
        self._text_pill(shown, FG)
        self._result_job = self.root.after(ms, self.show_idle)

    def hide(self):
        self.show_idle()

"""Clips tray - a small draggable panel with your 10 most recent transcriptions.

- Drag the header to move the panel anywhere; it stays on top.
- Drag a clip out into another app to drop the text there (when the optional
  tkinterdnd2 engine is available), or simply click a clip to copy it.
"""

import tkinter as tk
from tkinter import ttk

from . import history, theme

try:
    from tkinterdnd2 import DND_TEXT  # optional drag-out support
    HAS_DND = True
except Exception:
    HAS_DND = False


class ClipsTray:
    _open = None   # singleton

    @classmethod
    def toggle(cls, root):
        if cls._open is not None and cls._open.win.winfo_exists():
            cls._open.win.destroy()
            cls._open = None
        else:
            cls._open = cls(root)

    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=theme.PANEL)
        sw = self.win.winfo_screenwidth()
        self.win.geometry(f"340x420+{sw - 370}+120")

        header = tk.Frame(self.win, bg=theme.SIDEBAR, cursor="fleur")
        header.pack(fill="x")
        tk.Label(header, text="  📋  Clips — click a clip to paste it at your cursor",
                 bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI Semibold", 10), pady=8).pack(side="left")
        close = tk.Label(header, text=" ✕ ", bg=theme.SIDEBAR, fg=theme.DIM,
                         font=("Segoe UI", 11), cursor="hand2")
        close.pack(side="right", padx=6)
        close.bind("<Button-1>", lambda e: self._close())
        # bind drag on the header AND everything sitting on it (the title
        # label was swallowing clicks before - that was the "stuck" feeling)
        for w in (header, *header.winfo_children()):
            if w is close:
                continue
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        self._no_focus_steal()

        srow = tk.Frame(self.win, bg=theme.PANEL)
        srow.pack(fill="x", padx=8, pady=(8, 0))
        tk.Label(srow, text="🔍", bg=theme.PANEL, fg=theme.DIM).pack(side="left")
        self.search_var = tk.StringVar()
        se = tk.Entry(srow, textvariable=self.search_var, bg=theme.FIELD,
                      fg=theme.FG, insertbackground=theme.FG, borderwidth=0)
        se.pack(side="left", fill="x", expand=True, padx=6, ipady=4)
        se.bind("<KeyRelease>", lambda e: self.refresh())

        self.body = tk.Frame(self.win, bg=theme.PANEL)
        self.body.pack(fill="both", expand=True, padx=8, pady=8)
        self.status = tk.Label(self.win, text="", bg=theme.PANEL, fg=theme.DIM,
                               font=("Segoe UI", 9))
        self.status.pack(pady=(0, 6))
        self.refresh()

    def _no_focus_steal(self):
        """Clicks on the tray never move focus away from the user's app,
        so a clicked clip can paste straight into their cursor position."""
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

    # ---- window dragging ----
    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.win.winfo_x() + e.x - self._dx
        y = self.win.winfo_y() + e.y - self._dy
        self.win.geometry(f"+{x}+{y}")

    def _close(self):
        ClipsTray._open = None
        self.win.destroy()

    # ---- clips ----
    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        term = (self.search_var.get() if hasattr(self, "search_var") else "").strip().lower()
        entries = history.entries(limit=10)
        if not entries:
            tk.Label(self.body, text="No clips yet — dictate something!",
                     bg=theme.PANEL, fg=theme.DIM).pack(pady=20)
            return
        for e in entries:
            text = e.get("text", "")
            ts = e.get("ts")
            shown = text.replace("\n", " ")
            shown = shown if len(shown) <= 66 else shown[:63] + "…"
            hit = bool(term) and term in text.lower()
            bg = "#0a3d78" if hit else theme.FIELD
            row = tk.Frame(self.body, bg=bg)
            row.pack(fill="x", pady=3)
            lbl = tk.Label(row, text=" " + shown, anchor="w",
                           bg=bg, fg=theme.FG, font=("Segoe UI", 9),
                           wraplength=270, justify="left", pady=6, padx=6,
                           cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            x = tk.Label(row, text="✕", bg=bg, fg=theme.DIM,
                         font=("Segoe UI", 10), padx=8, cursor="hand2")
            x.pack(side="right")
            x.bind("<Button-1>", lambda ev, t=ts: self._delete(t))
            x.bind("<Enter>", lambda ev, w=x: w.configure(fg="#ff453a"))
            x.bind("<Leave>", lambda ev, w=x: w.configure(fg=theme.DIM))
            lbl.bind("<Button-1>", lambda ev, t=text: self._copy(t))
            if HAS_DND:
                try:
                    lbl.drag_source_register(1, DND_TEXT)
                    lbl.dnd_bind("<<DragInitCmd>>",
                                 lambda ev, t=text: ("copy", DND_TEXT, t))
                except Exception:
                    pass

    def _delete(self, ts):
        history.delete(ts)
        self.refresh()

    def _copy(self, text):
        """Click = paste directly where the user's cursor is."""
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            self.status.configure(text="Copy failed")
            return
        try:
            from . import injector
            injector.press_ctrl_v()
            self.status.configure(text="Pasted at your cursor ✓")
        except Exception:
            self.status.configure(text="Copied ✓ — Ctrl+V to paste")
        self.win.after(2000, lambda: self.status.configure(text=""))

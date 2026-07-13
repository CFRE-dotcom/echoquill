"""Clips tray - your 10 most recent transcriptions, always within reach.

- Click a clip: pastes into the app you were just working in, at its cursor.
- Press and DRAG a clip: carry it and release over any window - the text
  drops right where you let go (true drag-and-drop, no engine needed).
- Search box: type to highlight matching clips.
- ✕ deletes a clip. Drag the header to move the tray. Stays on top.
"""

import ctypes
import threading
import time
import tkinter as tk

from . import helptip, history, injector, theme

DRAG_THRESHOLD = 10  # pixels of movement that turn a click into a drag


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _cursor_pos():
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt


def _click_at_cursor():
    """Synthesize a left click where the cursor already is (sets the caret)."""
    MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class ClipsTray:
    _open = None   # singleton

    @classmethod
    def toggle(cls, root):
        if cls._open is not None:
            try:
                if cls._open.win.winfo_exists():
                    cls._open._close()
                    return
            except Exception:
                pass
        cls._open = cls(root)

    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=theme.PANEL)
        sw = self.win.winfo_screenwidth()
        self.win.geometry(f"340x440+{sw - 370}+120")

        header = tk.Frame(self.win, bg=theme.SIDEBAR, cursor="fleur")
        header.pack(fill="x")
        title = tk.Label(header, text="  📋  Clips — click to paste · drag to drop",
                         bg=theme.SIDEBAR, fg=theme.FG,
                         font=("Segoe UI Semibold", 10), pady=8)
        title.pack(side="left")
        close = tk.Label(header, text=" ✕ ", bg=theme.SIDEBAR, fg=theme.DIM,
                         font=("Segoe UI", 11), cursor="hand2")
        close.pack(side="right", padx=6)
        close.bind("<Button-1>", lambda e: self._close())
        helptip.tip(close, "Close the clips tray.")
        _help = ("How to use the Clips tray\n\n"
                 "• CLICK a clip — it pastes straight into whatever text field "
                 "your cursor is in (the app you were just using).\n"
                 "• DRAG a clip — press and hold, then drag it onto any window "
                 "to drop the text exactly where you let go.\n"
                 "• Search — type in the box to highlight clips that contain a word.\n"
                 "• ✕ — delete a clip you don't want.\n"
                 "• Drag the top bar to move this tray anywhere.\n\n"
                 "Pasting into a program and nothing happens? That app is probably "
                 "running as administrator. Turn on Settings → General → "
                 "Administrator mode, or set Insert text by → \"type\".")
        helptip.attach(self.win, header, "Clips tray — help", _help).pack(side="right", padx=4)
        for w in (header, title):
            w.bind("<Button-1>", self._win_drag_start)
            w.bind("<B1-Motion>", self._win_drag_move)

        srow = tk.Frame(self.win, bg=theme.PANEL)
        srow.pack(fill="x", padx=8, pady=(8, 0))
        from . import widgets
        _swrap, self._search_value = widgets.make_search(
            srow, "Search your clips…", self.refresh)
        _swrap.pack(fill="x")

        self.body = tk.Frame(self.win, bg=theme.PANEL)
        self.body.pack(fill="both", expand=True, padx=8, pady=8)
        self.status = tk.Label(self.win, text="", bg=theme.PANEL, fg=theme.DIM,
                               font=("Segoe UI", 9))
        self.status.pack(pady=(0, 6))

        # remember the app the user was in, so click-paste can return to it
        self._last_target = None
        self._watching = True
        threading.Thread(target=self._watch_foreground, daemon=True).start()
        self.win.bind("<Destroy>", lambda e: setattr(self, "_watching", False))

        self.refresh()

    # ---------- foreground tracking ----------

    def _own_hwnd(self):
        try:
            return ctypes.windll.user32.GetParent(self.win.winfo_id())
        except Exception:
            return None

    def _watch_foreground(self):
        u32 = ctypes.windll.user32
        while self._watching:
            try:
                fg = u32.GetForegroundWindow()
                if fg and fg != self._own_hwnd():
                    self._last_target = fg
            except Exception:
                pass
            time.sleep(0.4)

    # ---------- window dragging ----------

    def _win_drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _win_drag_move(self, e):
        self.win.geometry(f"+{self.win.winfo_x() + e.x - self._dx}"
                          f"+{self.win.winfo_y() + e.y - self._dy}")

    def _close(self):
        self._watching = False
        ClipsTray._open = None
        self.win.destroy()

    # ---------- clips ----------

    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        term = self._search_value().lower()
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
            lbl = tk.Label(row, text=" " + shown, anchor="w", bg=bg,
                           fg=theme.FG, font=("Segoe UI", 9), wraplength=270,
                           justify="left", pady=6, padx=6, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            ed = tk.Label(row, text="✎", bg=bg, fg=theme.DIM,
                          font=("Segoe UI", 10), padx=4, cursor="hand2")
            ed.pack(side="right")
            ed.bind("<Button-1>", lambda ev, t=text, ts2=ts: self._edit_clip(t, ts2))
            ed.bind("<Enter>", lambda ev, w=ed: w.configure(fg=theme.ACCENT))
            ed.bind("<Leave>", lambda ev, w=ed: w.configure(fg=theme.DIM))
            helptip.tip(ed, "Edit this clip (with Ask AI)")
            x = tk.Label(row, text="✕", bg=bg, fg=theme.DIM,
                         font=("Segoe UI", 10), padx=8, cursor="hand2")
            x.pack(side="right")
            x.bind("<Button-1>", lambda ev, t=ts: self._delete(t))
            x.bind("<Enter>", lambda ev, w=x: w.configure(fg="#ff453a"))
            x.bind("<Leave>", lambda ev, w=x: w.configure(fg=theme.DIM))
            helptip.tip(x, "Delete")
            # click = paste into last app · press-and-move = carry & drop
            lbl.bind("<ButtonPress-1>", lambda ev, t=text: self._press(ev, t))
            lbl.bind("<B1-Motion>", self._maybe_drag)
            lbl.bind("<ButtonRelease-1>", self._release)

    def _delete(self, ts):
        history.delete(ts)
        self.refresh()

    def _edit_clip(self, text, ts):
        from . import edit_dialog

        def _save(new_text):
            history.update(ts, new_text)
            self.refresh()
        cfg = getattr(self, "cfg", None)
        edit_dialog.open_editor(self.win, text, _save, cfg=cfg,
                                title="Edit clip", anchor=self.win)

    # ---------- click vs drag ----------

    def _press(self, e, text):
        self._drag_text = text
        self._press_x, self._press_y = e.x_root, e.y_root
        self._dragging = False

    def _maybe_drag(self, e):
        if not self._dragging and (abs(e.x_root - self._press_x) > DRAG_THRESHOLD
                                   or abs(e.y_root - self._press_y) > DRAG_THRESHOLD):
            self._dragging = True
            self.win.configure(cursor="hand2")
            self.status.configure(text="Carrying clip — release it over any text area")

    def _release(self, e):
        self.win.configure(cursor="")
        if not getattr(self, "_dragging", False):
            self._paste_to_last_app(self._drag_text)
            return
        self.status.configure(text="")
        # dropped: find the window under the cursor and paste at that spot
        try:
            pt = _cursor_pos()
            hwnd = ctypes.windll.user32.WindowFromPoint(pt)
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)  # GA_ROOT
            if not hwnd or root_hwnd == self._own_hwnd():
                self.status.configure(text="Dropped on the tray — click a clip to paste instead")
                return
            import pyperclip
            pyperclip.copy(self._drag_text)
            ctypes.windll.user32.SetForegroundWindow(root_hwnd)
            time.sleep(0.15)
            _click_at_cursor()          # place the caret where they dropped
            time.sleep(0.10)
            injector.press_ctrl_v()
            self.status.configure(text="Dropped ✓")
        except Exception:
            self.status.configure(text="Copied ✓ — Ctrl+V to paste")
        self.win.after(2200, lambda: self.status.configure(text=""))

    def _paste_to_last_app(self, text):
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            self.status.configure(text="Copy failed")
            return
        target = self._last_target
        if target:
            try:
                ctypes.windll.user32.SetForegroundWindow(target)
                time.sleep(0.20)
                injector.press_ctrl_v()
                self.status.configure(text="Pasted into your last app ✓")
            except Exception:
                self.status.configure(text="Copied ✓ — Ctrl+V to paste")
        else:
            self.status.configure(text="Copied ✓ — Ctrl+V to paste")
        self.win.after(2200, lambda: self.status.configure(text=""))

"""A small green 'update available' badge that appears in the top-right corner
when a new version is out. Hover shows the version; click opens the updater."""

import tkinter as tk

GREEN = "#30d158"
DARK = "#1c1c1e"
FG = "#f2f2f7"


class UpdateBadge:
    def __init__(self, root: tk.Tk, on_click):
        self.root = root
        self.on_click = on_click
        self.win = None
        self.tip = None
        self.version = ""

    def show(self, version: str):
        self.version = version
        if self.win is not None and self.win.winfo_exists():
            return
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.96)
        except Exception:
            pass
        self.win.configure(bg=GREEN)
        lbl = tk.Label(self.win, text="  ⬆  Update  ", bg=GREEN, fg="#00330f",
                       font=("Segoe UI Semibold", 10), cursor="hand2", pady=6)
        lbl.pack()
        for w in (self.win, lbl):
            w.bind("<Button-1>", self._clicked)
            w.bind("<Enter>", self._show_tip)
            w.bind("<Leave>", self._hide_tip)
        self._no_focus_steal()
        self._place()
        # gentle pulse so it draws the eye
        self._pulse(0)

    def _place(self):
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        w = self.win.winfo_reqwidth()
        self.win.geometry(f"+{sw - w - 18}+18")

    def _no_focus_steal(self):
        try:
            import ctypes
            self.win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x08000000 | 0x00000080)
        except Exception:
            pass

    def _pulse(self, step):
        if self.win is None or not self.win.winfo_exists():
            return
        try:
            self.win.attributes("-alpha", 0.75 + 0.22 * abs((step % 20) - 10) / 10)
        except Exception:
            pass
        self.win.after(120, lambda: self._pulse(step + 1))

    def _show_tip(self, _e=None):
        if self.tip is not None:
            return
        self.tip = tk.Toplevel(self.win)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=f"Update available (v{self.version}) — click to install",
                 bg=DARK, fg=FG, font=("Segoe UI", 9), padx=10, pady=6).pack()
        self.tip.update_idletasks()
        sw = self.tip.winfo_screenwidth()
        w = self.tip.winfo_reqwidth()
        self.tip.geometry(f"+{sw - w - 18}+56")

    def _hide_tip(self, _e=None):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

    def _clicked(self, _e=None):
        self._hide_tip()
        try:
            self.on_click()
        except Exception:
            pass

    def hide(self):
        self._hide_tip()
        if self.win is not None:
            self.win.destroy()
            self.win = None

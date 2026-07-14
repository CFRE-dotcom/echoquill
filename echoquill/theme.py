"""Theming for all EchoQuill windows - dark, light, or follow-system."""

import tkinter as tk
from tkinter import ttk

_DARK = dict(BG="#1c1c1e", PANEL="#232326", SIDEBAR="#141416", FG="#f2f2f7",
             DIM="#98989d", ACCENT="#0a84ff", FIELD="#2c2c2e", BORDER="#3a3a3c")
_LIGHT = dict(BG="#f5f5f7", PANEL="#ffffff", SIDEBAR="#e9e9ec", FG="#1c1c1e",
              DIM="#6b6b70", ACCENT="#0a84ff", FIELD="#ffffff", BORDER="#d0d0d5")

# active palette (module globals other files read as theme.BG etc.)
BG = _DARK["BG"]; PANEL = _DARK["PANEL"]; SIDEBAR = _DARK["SIDEBAR"]
FG = _DARK["FG"]; DIM = _DARK["DIM"]; ACCENT = _DARK["ACCENT"]
FIELD = _DARK["FIELD"]; BORDER = _DARK["BORDER"]

FONT = ("Segoe UI", 10)
FONT_SECTION = ("Segoe UI Semibold", 11)
FONT_TITLE = ("Segoe UI Semibold", 16)


def _system_prefers_light() -> bool:
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        val, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        return bool(val)
    except Exception:
        return False


def set_mode(mode: str):
    """mode: 'dark', 'light', or 'system'. Rebinds the active palette."""
    if mode == "system":
        pal = _LIGHT if _system_prefers_light() else _DARK
    elif mode == "light":
        pal = _LIGHT
    else:
        pal = _DARK
    g = globals()
    for k, v in pal.items():
        g[k] = v


def apply(win) -> ttk.Style:
    win.configure(bg=BG)
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(".", background=BG, foreground=FG,
                    fieldbackground=FIELD, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, font=FONT)
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("TLabel", background=BG, foreground=FG, font=FONT)
    style.configure("Dim.TLabel", background=BG, foreground=DIM)
    style.configure("Title.TLabel", background=BG, font=FONT_TITLE)
    style.configure("Section.TLabel", background=BG, foreground=DIM,
                    font=FONT_SECTION)
    style.configure("TCheckbutton", background=BG, foreground=FG, font=FONT)
    style.map("TCheckbutton",
              background=[("active", BG)],
              foreground=[("disabled", DIM)])
    style.configure("TButton", background=FIELD, foreground=FG,
                    borderwidth=0, padding=(14, 7))
    style.map("TButton", background=[("active", BORDER)])
    style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", "#3396ff")])
    style.configure("TEntry", fieldbackground=FIELD, foreground=FG,
                    insertcolor=FG, borderwidth=0, padding=6)
    style.configure("TCombobox", fieldbackground=FIELD, foreground=FG,
                    background=FIELD, arrowcolor=FG, borderwidth=0, padding=5)
    style.map("TCombobox",
              fieldbackground=[("readonly", FIELD)],
              foreground=[("readonly", FG)],
              background=[("readonly", FIELD)])
    style.configure("TSpinbox", fieldbackground=FIELD, foreground=FG,
                    background=FIELD, arrowcolor=FG, borderwidth=0)
    win.option_add("*TCombobox*Listbox.background", FIELD)
    win.option_add("*TCombobox*Listbox.foreground", FG)
    win.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    style.configure("Vertical.TScrollbar", background=FIELD, troughcolor=BG,
                    bordercolor=BG, arrowcolor=DIM)
    _install_context_menus(win)
    return style


class Scrollable(ttk.Frame):
    """A frame with a vertical scrollbar - put widgets in `.inner`."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        cid = self.canvas.create_window(0, 0, anchor="nw", window=self.inner)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            cid, width=e.width))
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all(
            "<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120), "units")


def _install_context_menus(win):
    """Right-click Cut/Copy/Paste on every entry and text box in this window."""
    def popup(event):
        w = event.widget
        m = tk.Menu(win, tearoff=0, bg=FIELD, fg=FG,
                    activebackground=ACCENT, activeforeground="#ffffff", bd=0)
        m.add_command(label="Cut", command=lambda: w.event_generate("<<Cut>>"))
        m.add_command(label="Copy", command=lambda: w.event_generate("<<Copy>>"))
        m.add_command(label="Paste", command=lambda: w.event_generate("<<Paste>>"))
        m.add_separator()
        m.add_command(label="Select all",
                      command=lambda: w.event_generate("<<SelectAll>>"))
        m.tk_popup(event.x_root, event.y_root)
        return "break"
    for cls in ("Entry", "TEntry", "Text", "TCombobox", "TSpinbox"):
        try:
            win.bind_class(cls, "<Button-3>", popup)
        except Exception:
            pass


def dark_listbox(parent, **kw) -> tk.Listbox:
    return tk.Listbox(parent, bg=FIELD, fg=FG, selectbackground=ACCENT,
                      selectforeground="#ffffff", borderwidth=0,
                      highlightthickness=0, font=FONT, **kw)


def dark_text(parent, **kw) -> tk.Text:
    """A dark Text with a REAL vertical scrollbar that auto-appears once the
    content grows past the box (like a normal editor)."""
    sb = ttk.Scrollbar(parent, orient="vertical")
    t = tk.Text(parent, bg=FIELD, fg=FG, insertbackground=FG,
                borderwidth=0, highlightthickness=0, font=FONT,
                padx=8, pady=6, **kw)

    def _yset(lo, hi):
        # show the bar only when there's something to scroll
        try:
            if float(lo) <= 0.0 and float(hi) >= 1.0:
                sb.pack_forget()
            elif not sb.winfo_ismapped():
                sb.pack(side="right", fill="y")
        except Exception:
            pass
        sb.set(lo, hi)

    t.configure(yscrollcommand=_yset)
    sb.configure(command=t.yview)

    def _wheel(e):
        t.yview_scroll(int(-e.delta / 120), "units")
        return "break"
    t.bind("<MouseWheel>", _wheel)
    return t

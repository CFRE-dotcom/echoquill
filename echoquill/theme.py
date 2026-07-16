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
    # One clean, always-visible scrollbar app-wide: no arrow buttons (one piece),
    # a medium-gray thumb that auto-sizes to the content (responsive) and shows
    # the accent colour while you drag it. Visible on both light and dark.
    def _is_light(hexcol):
        try:
            r = int(hexcol[1:3], 16); g = int(hexcol[3:5], 16); b = int(hexcol[5:7], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) > 150
        except Exception:
            return False
    _light = _is_light(BG)
    _thumb = ACCENT
    _trough = "#e5e5ea" if _light else "#242426"
    for _o in ("Vertical", "Horizontal"):
        _stick = "ns" if _o == "Vertical" else "we"
        try:
            style.layout(f"{_o}.TScrollbar", [
                (f"{_o}.Scrollbar.trough", {"sticky": "nswe", "children": [
                    (f"{_o}.Scrollbar.thumb",
                     {"expand": "1", "sticky": "nswe"})]})])
        except Exception:
            pass
    style.configure("Vertical.TScrollbar", troughcolor=_trough, background=_thumb,
                    bordercolor=_trough, lightcolor=_thumb, darkcolor=_thumb,
                    arrowcolor=_thumb, relief="flat", width=13)
    style.configure("Horizontal.TScrollbar", troughcolor=_trough, background=_thumb,
                    bordercolor=_trough, lightcolor=_thumb, darkcolor=_thumb,
                    arrowcolor=_thumb, relief="flat")
    for _o in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.map(_o, background=[("pressed", ACCENT), ("active", ACCENT)])
    # Bold, obvious scrollbar for the left menu (accent-blue, a touch wider) so
    # it's clear there's more to scroll - not the muted gray used elsewhere.
    try:
        style.layout("Sidebar.Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {"sticky": "nswe", "children": [
                ("Vertical.Scrollbar.thumb",
                 {"expand": "1", "sticky": "nswe"})]})])
    except Exception:
        pass
    style.configure("Sidebar.Vertical.TScrollbar", troughcolor=SIDEBAR,
                    background=ACCENT, bordercolor=SIDEBAR, lightcolor=ACCENT,
                    darkcolor=ACCENT, arrowcolor=ACCENT, relief="flat", width=14)
    style.map("Sidebar.Vertical.TScrollbar",
              background=[("pressed", "#3396ff"), ("active", "#3396ff")])
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
        # auto-hide: only show the scrollbar when the content actually overflows
        self._vsb = vsb
        self._vsb_shown = True

        def _autohide(_e=None):
            try:
                need = self.inner.winfo_reqheight() > self.canvas.winfo_height() + 1
            except Exception:
                return
            if need and not self._vsb_shown:
                vsb.pack(side="right", fill="y")
                self._vsb_shown = True
            elif not need and self._vsb_shown:
                vsb.pack_forget()
                self._vsb_shown = False
        self._autohide = _autohide
        self.inner.bind("<Configure>", lambda e: (self.canvas.configure(
            scrollregion=self.canvas.bbox("all")), _autohide()), add="+")
        self.canvas.bind("<Configure>", lambda e: _autohide(), add="+")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all(
            "<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120), "units")


def _clip_get_selection(w):
    """Selected text in an Entry or Text, or '' if nothing is selected."""
    try:
        return w.selection_get()
    except Exception:
        return ""


def _clip_delete_selection(w):
    try:
        w.delete("sel.first", "sel.last")
    except Exception:
        pass


def clip_copy(w):
    sel = _clip_get_selection(w)
    if sel:
        try:
            w.clipboard_clear(); w.clipboard_append(sel)
        except Exception:
            pass
    return "break"


def clip_cut(w):
    sel = _clip_get_selection(w)
    if sel:
        try:
            w.clipboard_clear(); w.clipboard_append(sel)
        except Exception:
            pass
        _clip_delete_selection(w)
    return "break"


def clip_paste(w):
    try:
        txt = w.clipboard_get()
    except Exception:
        txt = ""
    if txt:
        _clip_delete_selection(w)         # replace any selection
        try:
            w.insert("insert", txt)
        except Exception:
            pass
    return "break"


def clip_select_all(w):
    try:
        if isinstance(w, tk.Text):
            w.tag_add("sel", "1.0", "end-1c")
        else:
            w.select_range(0, "end")
            w.icursor("end")
    except Exception:
        pass
    return "break"


def _install_context_menus(win):
    """Right-click Cut/Copy/Paste on every entry and text box, app-wide.

    Handlers act on the widget and clipboard DIRECTLY (not via <<Copy>> virtual
    events), and the selection is captured the instant you right-click - before
    the menu can steal focus and clear it. Keyboard Ctrl+C/X/V/A are also bound
    at the class level so they never depend on Tk's default virtual-event wiring.
    """
    def popup(event):
        w = event.widget
        sel = _clip_get_selection(w)      # capture BEFORE the menu grabs focus
        has_sel = bool(sel)

        def _copy():
            if sel:
                try:
                    w.clipboard_clear(); w.clipboard_append(sel)
                except Exception:
                    pass

        def _cut():
            if sel:
                try:
                    w.clipboard_clear(); w.clipboard_append(sel)
                except Exception:
                    pass
                _clip_delete_selection(w)

        def _paste():
            try:
                w.focus_set()
            except Exception:
                pass
            clip_paste(w)

        try:
            _parent = w.winfo_toplevel()
        except Exception:
            _parent = w
        m = tk.Menu(_parent, tearoff=0, bg=FIELD, fg=FG,
                    activebackground=ACCENT, activeforeground="#ffffff", bd=0)
        m.add_command(label="Cut", command=_cut,
                      state=("normal" if has_sel else "disabled"))
        m.add_command(label="Copy", command=_copy,
                      state=("normal" if has_sel else "disabled"))
        m.add_command(label="Paste", command=_paste)
        m.add_separator()
        m.add_command(label="Select all", command=lambda: clip_select_all(w))
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
        return "break"

    for cls in ("Entry", "TEntry", "Text", "TCombobox", "TSpinbox"):
        for btn in ("<Button-3>", "<Button-2>"):
            try:
                win.bind_class(cls, btn, popup)
            except Exception:
                pass
        try:
            win.bind_class(cls, "<Control-c>", lambda e: clip_copy(e.widget))
            win.bind_class(cls, "<Control-C>", lambda e: clip_copy(e.widget))
            win.bind_class(cls, "<Control-x>", lambda e: clip_cut(e.widget))
            win.bind_class(cls, "<Control-X>", lambda e: clip_cut(e.widget))
            win.bind_class(cls, "<Control-v>", lambda e: clip_paste(e.widget))
            win.bind_class(cls, "<Control-V>", lambda e: clip_paste(e.widget))
            win.bind_class(cls, "<Control-a>", lambda e: clip_select_all(e.widget))
            win.bind_class(cls, "<Control-A>", lambda e: clip_select_all(e.widget))
        except Exception:
            pass


def dark_listbox(parent, **kw) -> tk.Listbox:
    return tk.Listbox(parent, bg=FIELD, fg=FG, selectbackground=ACCENT,
                      selectforeground="#ffffff", borderwidth=0,
                      highlightthickness=0, font=FONT, **kw)


def dark_text(parent, **kw) -> tk.Text:
    """Dark Text with a real, always-visible right-side scrollbar.

    Text + Scrollbar live in a wrapper frame; the Text's pack/grid/place are
    rebound to the wrapper so existing callers (which .pack() the return value)
    lay out the whole thing. No packing happens in a scroll callback, so it
    can't cause the geometry loop that froze earlier builds."""
    wrap = ttk.Frame(parent)
    sb = ttk.Scrollbar(wrap, orient="vertical")
    t = tk.Text(wrap, bg=FIELD, fg=FG, insertbackground=FG,
                borderwidth=0, highlightthickness=0, font=FONT,
                padx=8, pady=6, yscrollcommand=sb.set, **kw)
    sb.configure(command=t.yview)
    sb.pack(side="right", fill="y")
    t.pack(side="left", fill="both", expand=True)

    def _wheel(e):
        t.yview_scroll(int(-e.delta / 120), "units")
        return "break"
    t.bind("<MouseWheel>", _wheel)

    # make the returned Text lay out its wrapper (so callers' .pack() works)
    t.pack = wrap.pack
    t.grid = wrap.grid
    t.place = wrap.place
    t.pack_forget = wrap.pack_forget
    t.grid_forget = wrap.grid_forget
    return t

"""Hover help: a '?' icon with a how-to popover, and tip() for any widget.

Rules: only ONE tooltip is ever open app-wide, and it always closes when the
pointer leaves the widget (a short poll catches missed <Leave> events, e.g.
inside scrolling lists)."""

import tkinter as tk

from . import theme

# single global tooltip state — guarantees only one is ever visible
_S = {"tip": None, "after": None, "owner": None}


def _pointer_over(widget) -> bool:
    try:
        px, py = widget.winfo_pointerxy()
        wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
        ww, wh = widget.winfo_width(), widget.winfo_height()
        return wx <= px <= wx + ww and wy <= py <= wy + wh
    except Exception:
        return False


def _hide_now():
    owner = _S.get("owner")
    if _S.get("after") is not None and owner is not None:
        try:
            owner.after_cancel(_S["after"])
        except Exception:
            pass
    _S["after"] = None
    if _S.get("tip") is not None:
        try:
            _S["tip"].destroy()
        except Exception:
            pass
    _S["tip"] = None
    _S["owner"] = None


def _bind_tooltip(widget, render):
    def _poll():
        if _S.get("tip") is None or _S.get("owner") is not widget:
            return
        if not _pointer_over(widget):
            _hide_now()
            return
        try:
            widget.after(200, _poll)
        except Exception:
            pass

    def _do_show():
        _S["after"] = None
        if not _pointer_over(widget):
            return
        _hide_now()                      # ensure only one exists
        t = tk.Toplevel(widget)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        try:
            t.attributes("-alpha", 0.98)
        except Exception:
            pass
        render(t)
        t.update_idletasks()
        px, py = widget.winfo_pointerxy()
        x, y = px + 14, py + 20
        sw, sh = t.winfo_screenwidth(), t.winfo_screenheight()
        w, h = t.winfo_reqwidth(), t.winfo_reqheight()
        if x + w > sw - 8:
            x = max(8, sw - w - 8)
        if y + h > sh - 8:
            y = max(8, py - h - 12)
        t.geometry(f"+{int(x)}+{int(y)}")
        _S["tip"] = t
        _S["owner"] = widget
        _poll()

    def show(_e=None):
        _hide_now()
        try:
            _S["owner"] = widget
            _S["after"] = widget.after(250, _do_show)
        except Exception:
            pass

    def hide(_e=None):
        _hide_now()

    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", hide, add="+")
    widget.bind("<Button-1>", hide, add="+")
    widget.bind("<Destroy>", lambda e: _hide_now(), add="+")
    return widget


def tip(widget, text):
    """Attach a hover tooltip to ANY widget."""
    def render(t):
        tk.Label(t, text=text, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI", 9), justify="left", wraplength=320,
                 padx=9, pady=6, highlightthickness=1,
                 highlightbackground=theme.ACCENT).pack()
    return _bind_tooltip(widget, render)


def attach(parent_win, container, title, text):
    """Add a small blue '?' to `container`; hovering shows a readable how-to."""
    lbl = tk.Label(container, text=" ? ", bg=theme.ACCENT, fg="#ffffff",
                   font=("Segoe UI Semibold", 9), cursor="question_arrow")

    def render(t):
        frm = tk.Frame(t, bg=theme.SIDEBAR, highlightthickness=1,
                       highlightbackground=theme.ACCENT)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text=title, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI Semibold", 10), justify="left"
                 ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(frm, text=text, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI", 9), justify="left", wraplength=400
                 ).pack(anchor="w", padx=12, pady=(0, 10))

    _bind_tooltip(lbl, render)
    return lbl


def menu_hover(menu, items_getter):
    """Show the FULL text of a dropdown item while the pointer is over it.

    `menu` is the underlying tk.Menu of a ttk.OptionMenu (opt["menu"]).
    `items_getter()` returns the full-length item strings, in the same order
    the menu entries were added, so a truncated entry can still be read in full.
    """
    state = {"tip": None}

    def _hide():
        if state["tip"] is not None:
            try:
                state["tip"].destroy()
            except Exception:
                pass
            state["tip"] = None

    def _on_select(_e=None):
        try:
            idx = menu.index("active")
        except Exception:
            idx = None
        items = items_getter() or []
        off = 0
        try:
            if menu.type(0) == "tearoff":
                off = 1
        except Exception:
            pass
        pos = idx - off if isinstance(idx, int) else None
        if pos is None or pos < 0 or pos >= len(items):
            _hide()
            return
        full = items[pos]
        _hide()
        try:
            t = tk.Toplevel(menu)
            t.overrideredirect(True)
            t.attributes("-topmost", True)
            tk.Label(t, text=full, bg=theme.FIELD, fg=theme.FG, justify="left",
                     wraplength=460, borderwidth=1, relief="solid",
                     font=("Segoe UI", 9), padx=7, pady=4).pack()
            t.geometry(f"+{menu.winfo_pointerx() + 16}+{menu.winfo_pointery() + 12}")
            state["tip"] = t
        except Exception:
            pass

    menu.bind("<<MenuSelect>>", _on_select, add="+")
    menu.bind("<Unmap>", lambda e: _hide(), add="+")
    menu.bind("<Leave>", lambda e: _hide(), add="+")
    menu.bind("<Destroy>", lambda e: _hide(), add="+")

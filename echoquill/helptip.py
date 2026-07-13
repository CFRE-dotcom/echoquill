"""Hover help: a '?' icon with a how-to popover, and tip() for any widget.

Robust against the 'tooltip maps -> spurious <Leave> -> tooltip vanishes'
problem that happens for small widgets inside scrolling canvases: we only
hide when the pointer is genuinely off the widget (and off the tooltip)."""

import tkinter as tk

from . import theme


def _pointer_over(widget) -> bool:
    try:
        px, py = widget.winfo_pointerxy()
        wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
        ww, wh = widget.winfo_width(), widget.winfo_height()
        return wx <= px <= wx + ww and wy <= py <= wy + wh
    except Exception:
        return False


def _bind_tooltip(widget, render):
    """render(toplevel) fills the tooltip. Shows on hover, hides on real exit."""
    st = {"tip": None, "after": None}

    def do_show():
        st["after"] = None
        if st["tip"] is not None or not _pointer_over(widget):
            return
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
        x, y = px + 14, py + 20                     # offset from cursor
        sw, sh = t.winfo_screenwidth(), t.winfo_screenheight()
        w, h = t.winfo_reqwidth(), t.winfo_reqheight()
        if x + w > sw - 8:
            x = max(8, sw - w - 8)
        if y + h > sh - 8:
            y = max(8, py - h - 12)
        t.geometry(f"+{int(x)}+{int(y)}")
        st["tip"] = t

    def show(_e=None):
        if st["after"] is None and st["tip"] is None:
            st["after"] = widget.after(250, do_show)

    def hide(_e=None):
        # ignore the spurious <Leave> fired when the tooltip window maps
        if _pointer_over(widget):
            return
        if st["after"] is not None:
            try:
                widget.after_cancel(st["after"])
            except Exception:
                pass
            st["after"] = None
        if st["tip"] is not None:
            try:
                st["tip"].destroy()
            except Exception:
                pass
            st["tip"] = None

    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", hide, add="+")
    widget.bind("<Button-1>", hide, add="+")
    widget.bind("<Destroy>", lambda e: hide(), add="+")
    return widget


def tip(widget, text):
    """Attach a hover tooltip to ANY widget (buttons, entries, icons, labels)."""
    def render(t):
        tk.Label(t, text=text, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI", 9), justify="left", wraplength=320,
                 padx=9, pady=6, highlightthickness=1,
                 highlightbackground=theme.ACCENT).pack()
    return _bind_tooltip(widget, render)


def attach(parent_win, container, title, text):
    """Add a small '?' to `container`; hovering shows a readable how-to."""
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

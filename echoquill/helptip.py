"""Small '?' help icon that reveals a readable tooltip on HOVER (no click)."""

import tkinter as tk

from . import theme


def attach(parent_win, container, title, text):
    """Add a small '?' to `container`. Hovering it shows a readable tooltip;
    moving away hides it. Returns the label so callers can .pack()/.grid() it."""
    lbl = tk.Label(container, text=" ? ", bg=theme.ACCENT, fg="#ffffff",
                   font=("Segoe UI Semibold", 9), cursor="question_arrow")
    state = {"tip": None}

    def show(_e=None):
        if state["tip"] is not None:
            return
        lbl.configure(bg="#3396ff")
        t = tk.Toplevel(parent_win)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        frm = tk.Frame(t, bg=theme.SIDEBAR, highlightthickness=1,
                       highlightbackground=theme.ACCENT)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text=title, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI Semibold", 10), justify="left"
                 ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(frm, text=text, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI", 9), justify="left", wraplength=400
                 ).pack(anchor="w", padx=12, pady=(0, 10))
        t.update_idletasks()
        x = lbl.winfo_rootx()
        y = lbl.winfo_rooty() + lbl.winfo_height() + 4
        sw, sh = t.winfo_screenwidth(), t.winfo_screenheight()
        w, h = t.winfo_reqwidth(), t.winfo_reqheight()
        if x + w > sw - 8:
            x = max(8, sw - w - 8)
        if y + h > sh - 8:                      # not enough room below -> above
            y = max(8, lbl.winfo_rooty() - h - 4)
        t.geometry(f"+{int(x)}+{int(y)}")
        state["tip"] = t

    def hide(_e=None):
        lbl.configure(bg=theme.ACCENT)
        if state["tip"] is not None:
            try:
                state["tip"].destroy()
            except Exception:
                pass
            state["tip"] = None

    lbl.bind("<Enter>", show)
    lbl.bind("<Leave>", hide)
    return lbl
